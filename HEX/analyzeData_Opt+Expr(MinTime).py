import csv
import re
import pandas as pd
from collections import defaultdict

REPEAT_NUM = 1

filePath = './Data/100MB_10GB/'

eeop_file_path   = str(filePath) + 'expr_eeops.txt'
expr_file_path   = str(filePath) + 'report.csv'
opt_file_path    = str(filePath) + 'operator.csv'
jit_file_path    = str(filePath) + 'jit.csv'
factor_file_path = './Model/Factor/factors.csv'
output_file_path = './Output/level_vectors.csv'

# 定义EEOP名称列表
eeop_names = [
    "EEOP_DONE", "EEOP_INNER_FETCHSOME", "EEOP_OUTER_FETCHSOME", "EEOP_SCAN_FETCHSOME",
    "EEOP_INNER_VAR", "EEOP_OUTER_VAR", "EEOP_SCAN_VAR", "EEOP_INNER_SYSVAR", "EEOP_OUTER_SYSVAR",
    "EEOP_SCAN_SYSVAR", "EEOP_WHOLEROW", "EEOP_ASSIGN_INNER_VAR", "EEOP_ASSIGN_OUTER_VAR",
    "EEOP_ASSIGN_SCAN_VAR", "EEOP_ASSIGN_TMP", "EEOP_ASSIGN_TMP_MAKE_RO", "EEOP_CONST",
    "EEOP_FUNCEXPR", "EEOP_FUNCEXPR_STRICT", "EEOP_FUNCEXPR_FUSAGE", "EEOP_FUNCEXPR_STRICT_FUSAGE",
    "EEOP_BOOL_AND_STEP_FIRST", "EEOP_BOOL_AND_STEP", "EEOP_BOOL_AND_STEP_LAST",
    "EEOP_BOOL_OR_STEP_FIRST", "EEOP_BOOL_OR_STEP", "EEOP_BOOL_OR_STEP_LAST", "EEOP_BOOL_NOT_STEP",
    "EEOP_QUAL", "EEOP_JUMP", "EEOP_JUMP_IF_NULL", "EEOP_JUMP_IF_NOT_NULL", "EEOP_JUMP_IF_NOT_TRUE",
    "EEOP_NULLTEST_ISNULL", "EEOP_NULLTEST_ISNOTNULL", "EEOP_NULLTEST_ROWISNULL",
    "EEOP_NULLTEST_ROWISNOTNULL", "EEOP_BOOLTEST_IS_TRUE", "EEOP_BOOLTEST_IS_NOT_TRUE",
    "EEOP_BOOLTEST_IS_FALSE", "EEOP_BOOLTEST_IS_NOT_FALSE", "EEOP_PARAM_EXEC", "EEOP_PARAM_EXTERN",
    "EEOP_PARAM_CALLBACK", "EEOP_CASE_TESTVAL", "EEOP_MAKE_READONLY", "EEOP_IOCOERCE", "EEOP_DISTINCT",
    "EEOP_NOT_DISTINCT", "EEOP_NULLIF", "EEOP_SQLVALUEFUNCTION", "EEOP_CURRENTOFEXPR", "EEOP_NEXTVALUEEXPR",
    "EEOP_ARRAYEXPR", "EEOP_ARRAYCOERCE", "EEOP_ROW", "EEOP_ROWCOMPARE_STEP", "EEOP_ROWCOMPARE_FINAL",
    "EEOP_MINMAX", "EEOP_FIELDSELECT", "EEOP_FIELDSTORE_DEFORM", "EEOP_FIELDSTORE_FORM",
    "EEOP_SBSREF_SUBSCRIPT", "EEOP_SBSREF_OLD", "EEOP_SBSREF_ASSIGN", "EEOP_SBSREF_FETCH",
    "EEOP_DOMAIN_TESTVAL", "EEOP_DOMAIN_NOTNULL", "EEOP_DOMAIN_CHECK", "EEOP_CONVERT_ROWTYPE",
    "EEOP_SCALARARRAYOP", "EEOP_XMLEXPR", "EEOP_AGGREF", "EEOP_GROUPING_FUNC", "EEOP_WINDOW_FUNC",
    "EEOP_SUBPLAN", "EEOP_ALTERNATIVE_SUBPLAN", "EEOP_AGG_STRICT_DESERIALIZE", "EEOP_AGG_DESERIALIZE",
    "EEOP_AGG_STRICT_INPUT_CHECK_ARGS", "EEOP_AGG_STRICT_INPUT_CHECK_NULLS", "EEOP_AGG_PLAIN_PERGROUP_NULLCHECK",
    "EEOP_AGG_PLAIN_TRANS_INIT_STRICT_BYVAL", "EEOP_AGG_PLAIN_TRANS_STRICT_BYVAL", "EEOP_AGG_PLAIN_TRANS_BYVAL",
    "EEOP_AGG_PLAIN_TRANS_INIT_STRICT_BYREF", "EEOP_AGG_PLAIN_TRANS_STRICT_BYREF", "EEOP_AGG_PLAIN_TRANS_BYREF",
    "EEOP_AGG_ORDERED_TRANS_DATUM", "EEOP_AGG_ORDERED_TRANS_TUPLE", "EEOP_LAST"
]

# 使用enumerate创建eeop字典
eeop_map = {name: idx for idx, name in enumerate(eeop_names)}

# 获取EEOP因子及其平均值
eeop_factors    =   {}
avg_factor      =   0.0
with open(factor_file_path, mode='r', encoding='utf-8') as ffile:
    f_lines = [row for row in csv.reader(ffile) if any(row)]
    for line in f_lines:
        eeop                    =       str(line[0])
        factor                  =       float(line[1])
        eeop_factors[eeop]      =       factor
    if len(eeop_factors) > 0:
        avg_factor  =   float(sum(eeop_factors.values())/len(eeop_factors))

# expr-eeops字典,用于存储表达式编号和对应的EEOP步骤
expr_eeops = {}
database_idx = -1
database_names = ['tpch_0_1_0', 'tpch_0_2_0', 'tpch_0_3_0', 'tpch_0_4_0', 'tpch_0_5_0', 'tpch_0_6_0', 'tpch_0_7_0', 'tpch_0_8_0', 'tpch_0_9_0', 'tpch_1_0_0', 'tpch_2_0_0', 'tpch_3_0_0', 'tpch_4_0_0', 'tpch_5_0_0', 'tpch_6_0_0', 'tpch_7_0_0', 'tpch_8_0_0', 'tpch_9_0_0', 'tpch_10_0_0']
with open(eeop_file_path, mode='r', encoding='utf-8') as eefile:
    for line in eefile:
        line = line.strip()
        # 使用冒号分割行，将编号和EEOP分开
        if ':' in line:
            expr_id_part, eeops_part = line.split(':', 1)       # 分割成 "表达式编号 X" 和 "EEOP_***"
            expr_id = int(expr_id_part.split()[1])              # 提取编号并去除前缀文字，转换成整数
            if expr_id == 1:
                database_idx = database_idx + 1
                expr_eeops[database_names[database_idx]] = {}
            eeops = eeops_part.strip().split()                          # 将EEOP步骤拆分为一个列表
            expr_eeops[database_names[database_idx]][expr_id] = eeops   # 将编号和EEOP列表存入字典

# 每个表达式的EEOP计数
eeop_count = {}
for db in expr_eeops:
    eeop_count[db] = {}
    for expr in expr_eeops[db]:
        if expr not in eeop_count[db]:
            eeop_count[db][expr] = defaultdict(int)
        for eeop in expr_eeops[db][expr]:
            eeop_count[db][expr][eeop] += 1

# 表达式向量
expr_vectors = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
    'expr_count': 0,
    'opt_id': 0,
    'opt_type': "T_Invalid",
    'startup_cost': 0.0,
    'total_cost': 0.0,
    'startup_time': 0.0,
    'total_time': 0.0,
    'input_rows': 0,
    'output_rows': 0,
    'filtered_rows': 0,
    'left_opt_id': 0,
    'left_opt_type': "T_Invalid",
    'left_scost': 0.0,
    'left_tcost': 0.0,
    'left_actual_rows': 0,
    'left_total_time': 0.0,
    'right_opt_id': 0,
    'right_opt_type': "T_Invalid",
    'right_scost': 0.0,
    'right_tcost': 0.0,
    'right_actual_rows': 0,
    'right_total_time': 0.0,
    'best_level': 0,
    'eeop_steps': defaultdict(float)
})))

# 打开文件
with open(jit_file_path, mode="r", encoding='utf-8') as jFile, \
     open(expr_file_path, mode="r", encoding='utf-8') as eFile, \
     open(opt_file_path, mode="r", encoding='utf-8') as oFile:

    # 读取 jFile 和 eFile 的每一行
    j_lines = [row for row in csv.reader(jFile) if any(row)]
    e_lines = [row for row in csv.reader(eFile) if any(row)]

    # 分块读取 oFile 每个 SQL 语句的信息
    o_reader = csv.reader(oFile)

    o_block = []
    sql_operators = []

    for line in o_reader:
        if any(line):  # 非空行，添加到当前块
            o_block.append(line)
        else:  # 空行，表示新的 SQL 语句开始
            if o_block:
                sql_operators.append(o_block)
                o_block = []

    # 将最后的 o_block 添加到列表（防止文件最后一行没有空行的情况）
    if o_block:
        sql_operators.append(o_block)

    # 确保三者的行数一致
    if len(j_lines) != len(sql_operators) or len(e_lines) != len(sql_operators):
        print("j_lines = " + str(len(j_lines)) + ", e_lines = " + str(len(e_lines)) + ", sql_operators = " + str(len(sql_operators)))
        raise ValueError("The number of SQL statements are inconsistent. Please recheck the files.")

    # 依次遍历每个 SQL 语句的信息
    sql_expr_level_list = {}
    min_time = 0.0
    for j_line, sql_opts, e_line in zip(j_lines, sql_operators, e_lines):
        current_sql = re.sub(r"[ \t]+", " ", str(e_line[0])).strip()
        current_db = str(e_line[1]).strip()
        current_exec_time    =   float(j_line[-1])
        current_plan_time    =   float(j_line[-2])
        current_expr    =   []
        current_level   =   []
        for i in range(0, int((len(j_line)-2)/6)):
            temp_expr       =   []
            j_expr_id       =   int(j_line[6*i])
            j_expr_level    =   int(j_line[6*i+1])
            j_opt_id        =   int(j_line[6*i+2])
            j_opt_type      =   str(j_line[6*i+3])
            j_opt_scost     =   float(j_line[6*i+4])
            j_opt_tcost     =   float(j_line[6*i+5])
            temp_expr.append(j_expr_id)
            temp_expr.append(j_opt_id)
            temp_expr.append(j_opt_type)
            temp_expr.append(j_opt_scost)
            temp_expr.append(j_opt_tcost)
            current_expr.append(tuple(temp_expr))
            current_level.append(j_expr_level)

        updateLevel = False

        if tuple(current_expr) not in sql_expr_level_list:
            min_time = 0.0
            sql_expr_level_list[tuple(current_expr)] = []

        if min_time == 0.0 or current_exec_time < min_time:
            min_time = current_exec_time
            updateLevel = True
            sql_expr_level_list[tuple(current_expr)] = current_level

        current_opts = {}
        current_opts[(0, 'T_Invalid', 0.0, 0.0)] = [0, 'T_Invalid', 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0, 'T_Invalid', 0.0, 0.0, 0, 'T_Invalid', 0.0, 0.0]
        for opt in sql_opts:
            opt_id      = int(opt[0])
            opt_type    = str(opt[1])
            opt_scost   = float(opt[2])
            opt_tcost   = float(opt[3])
            current_opts[(opt_id, opt_type, opt_scost, opt_tcost)] = opt

        # print(str(len(current_expr)) + " " + str(len(e_line)))
        if updateLevel:
            for j in range(0, int((len(e_line) - 2) / 6)):
                expr_id             = int(e_line[6 * j + 2])
                expr_count          = int(e_line[6 * j + 3])
                expr_opt_id         = int(e_line[6 * j + 4])
                expr_opt_type       = str(e_line[6 * j + 5])
                expr_opt_scost      = float(e_line[6 * j + 6])
                expr_opt_tcost      = float(e_line[6 * j + 7])

                left_opt_id      =  int(current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)][9])
                left_opt_type    =  str(current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)][10])
                left_opt_scost   =  float(current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)][11])
                left_opt_tcost   =  float(current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)][12])
                right_opt_id     =  int(current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)][13])
                right_opt_type   =  str(current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)][14])
                right_opt_scost  =  float(current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)][15])
                right_opt_tcost  =  float(current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)][16])

                current_opt =   current_opts[(expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost)]
                left_opt    =   current_opts[(left_opt_id, left_opt_type, left_opt_scost, left_opt_tcost)]
                right_opt   =   current_opts[(right_opt_id, right_opt_type, right_opt_scost, right_opt_tcost)]

                if expr_count != 0:
                    expr_vectors[current_db][current_sql][expr_id]["expr_count"]    = int(expr_count)

                expr_vectors[current_db][current_sql][expr_id]["opt_id"]        = int(current_opt[0])
                expr_vectors[current_db][current_sql][expr_id]["opt_type"]      = str(current_opt[1])
                expr_vectors[current_db][current_sql][expr_id]["startup_cost"]  = float(current_opt[2])
                expr_vectors[current_db][current_sql][expr_id]["total_cost"]    = float(current_opt[3])

                if "Join" in expr_opt_type or "NestLoop" in expr_opt_type:
                    expr_vectors[current_db][current_sql][expr_id]["input_rows"] = max(int(left_opt[5]), int(right_opt[5]))
                elif "Scan" in expr_opt_type:
                    expr_vectors[current_db][current_sql][expr_id]["input_rows"] = int(current_opt[4])
                else:
                    expr_vectors[current_db][current_sql][expr_id]["input_rows"] = int(current_opt[4]) + int(left_opt[5]) + int(right_opt[5])

                expr_vectors[current_db][current_sql][expr_id]["output_rows"]   = int(current_opt[5])
                expr_vectors[current_db][current_sql][expr_id]["filtered_rows"] = int(current_opt[6])
                expr_vectors[current_db][current_sql][expr_id]["startup_time"]  = float(current_opt[7])
                expr_vectors[current_db][current_sql][expr_id]["total_time"]    = float(current_opt[8])
                expr_vectors[current_db][current_sql][expr_id]["left_opt_id"]   = int(left_opt[0])
                expr_vectors[current_db][current_sql][expr_id]["left_opt_type"] = str(left_opt[1])
                expr_vectors[current_db][current_sql][expr_id]["left_scost"]    = float(left_opt[2])
                expr_vectors[current_db][current_sql][expr_id]["left_tcost"]    = float(left_opt[3])
                expr_vectors[current_db][current_sql][expr_id]["left_actual_rows"]  = int(left_opt[5])
                expr_vectors[current_db][current_sql][expr_id]["left_total_time"]   = float(left_opt[8])
                expr_vectors[current_db][current_sql][expr_id]["right_opt_id"]      = int(right_opt[0])
                expr_vectors[current_db][current_sql][expr_id]["right_opt_type"]    = str(right_opt[1])
                expr_vectors[current_db][current_sql][expr_id]["right_scost"]       = float(right_opt[2])
                expr_vectors[current_db][current_sql][expr_id]["right_tcost"]       = float(right_opt[3])
                expr_vectors[current_db][current_sql][expr_id]["right_actual_rows"] = int(right_opt[5])
                expr_vectors[current_db][current_sql][expr_id]["right_total_time"]  = float(right_opt[8])
                for i in range(len(current_expr)):
                    if int(current_expr[i][0]) == expr_id and int(current_expr[i][1]) == expr_opt_id and str(current_expr[i][2]) == expr_opt_type and float(current_expr[i][3]) == expr_opt_scost and float(current_expr[i][4]) == expr_opt_tcost:
                        expr_vectors[current_db][current_sql][expr_id]["best_level"]        = int(current_level[j])

    # 输出向量信息
    # 写入到CSV文件
    with open(output_file_path, 'w+', newline='', encoding='gbk') as csvfile:
        # 创建 CSV 写入器
        fieldnames = ['查询语句', '数据库名', '表达式编号', '表达式次数', '最优级别', '算子编号', '算子类型', '启动Cost', '总Cost', '算子启动时间', '算子总时间',
                      '输入行数', '输出行数', '过滤行数', '左子树算子编号', '左子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间', '右子树算子编号',
                      '右子树类型', '右子树启动Cost', '右子树总Cost', '右子树输出行数', '右子树总时间'] + [f'{step}' for step in eeop_names]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # 写入表头
        writer.writeheader()

        for db in expr_vectors:
            for sql in expr_vectors[db]:
                for expr in expr_vectors[db][sql]:
                    if expr in expr_eeops[db]:
                        row = {}
                        row["数据库名"] = db
                        row["查询语句"] = sql
                        row["表达式编号"] = expr
                        row["表达式次数"] = expr_vectors[db][sql][expr]["expr_count"]
                        row["最优级别"] = expr_vectors[db][sql][expr]["best_level"]
                        row["算子编号"] = expr_vectors[db][sql][expr]["opt_id"]
                        row["算子类型"] = expr_vectors[db][sql][expr]["opt_type"]
                        row["启动Cost"] = expr_vectors[db][sql][expr]["startup_cost"]
                        row["总Cost"] = expr_vectors[db][sql][expr]["total_cost"]
                        row["算子启动时间"]  = expr_vectors[db][sql][expr]["startup_time"]
                        row["算子总时间"] = expr_vectors[db][sql][expr]["total_time"]
                        row["输入行数"] = expr_vectors[db][sql][expr]["input_rows"]
                        row["输出行数"] = expr_vectors[db][sql][expr]["output_rows"]
                        row["过滤行数"] = expr_vectors[db][sql][expr]["filtered_rows"]
                        row["左子树算子编号"] = expr_vectors[db][sql][expr]["left_opt_id"]
                        row["左子树类型"] = expr_vectors[db][sql][expr]["left_opt_type"]
                        row["左子树启动Cost"] = expr_vectors[db][sql][expr]["left_scost"]
                        row["左子树总Cost"] = expr_vectors[db][sql][expr]["left_tcost"]
                        row["左子树输出行数"] = expr_vectors[db][sql][expr]["left_actual_rows"]
                        row["左子树总时间"] = expr_vectors[db][sql][expr]["left_total_time"]
                        row["右子树算子编号"] = expr_vectors[db][sql][expr]["right_opt_id"]
                        row["右子树类型"] = expr_vectors[db][sql][expr]["right_opt_type"]
                        row["右子树启动Cost"] = expr_vectors[db][sql][expr]["right_scost"]
                        row["右子树总Cost"] = expr_vectors[db][sql][expr]["right_tcost"]
                        row["右子树输出行数"] = expr_vectors[db][sql][expr]["right_actual_rows"]
                        row["右子树总时间"] = expr_vectors[db][sql][expr]["right_total_time"]
                        for step in eeop_names:
                            if step == "EEOP_DONE" or step not in eeop_count[db][expr]:
                                row[step] = 0.0
                            elif step in eeop_factors:
                                row[step] = float(eeop_count[db][expr][step]) * float(row["表达式次数"]) * float(eeop_factors[step])
                            else:
                                row[step] = float(eeop_count[db][expr][step]) * float(row["表达式次数"]) * float(avg_factor)
                                print("No factor:", step)
                        writer.writerow(row)
                    else:
                        print("Expression " + str(expr) + " in " + str(db) + " not recognized!")
