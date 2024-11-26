import csv
import re
import pandas as pd
from collections import defaultdict

filePath = './Data/100MB_10GB/'

# eeop_file_path = './Data/100MB_6GB/expr_eeops.txt'
eeop_file_path = str(filePath) + 'expr_eeops.txt'
expr_file_path = str(filePath) + 'report.csv'
opt_file_path  = str(filePath) + 'operator.csv'
jit_file_path  = str(filePath) + 'jit.csv'
output_file_path = './Output/time_vectors.csv'

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
opt_vectors = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
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
    'eeop_count': defaultdict(int)
})))

# 打开文件
print("Processing All the data.")
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


    # 先写入文件列头
    fieldnames = ['查询语句', '数据库名', '算子编号', '算子类型', '启动Cost', '总Cost', '算子启动时间', '算子总时间', '输入行数', '输出行数', '过滤行数', '左子树算子编号',
                  '左子树类型', '左子树启动Cost', '左子树总Cost', '左子树输出行数', '左子树总时间', '右子树算子编号', '右子树类型', '右子树启动Cost', '右子树总Cost',
                  '右子树输出行数', '右子树总时间'] + [f'{step}' for step in eeop_names]
    # + [f'{opt}' for opt in opt_list]
    with open(output_file_path, 'w+', newline='', encoding='gbk') as csvfile:
        # 创建 CSV 写入器
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # 写入表头
        writer.writeheader()

    # # 加载所有算子信息
    # print("Processing Operator Info.")
    # opt_list = []
    # for opt_block in sql_operators:
    #     for opt in opt_block:
    #         if opt[0] not in opt_list:
    #             opt_list.append(str(opt[1]))
    # # 记录每个语句所有算子的Cost信息
    # line_num = 0
    # last_sql = ""
    # db_sql_opt_costs = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    # print("Processing Operator Cost.")
    # for sql_opts, e_line in zip(sql_operators, e_lines):
    #     print(line_num)
    #     line_num = line_num + 1
    #     current_sql = re.sub(r"[ \t]+", " ", str(e_line[0])).strip()
    #     current_db = str(e_line[1]).strip()
    #     if last_sql != current_sql:
    #         line_num = 1
    #         last_sql = current_sql
    #     if line_num  == 1:
    #         for opt in sql_opts:
    #             left_opt_id      =  int(opt[9])
    #             left_opt_type    =  str(opt[10])
    #             left_opt_scost   =  float(opt[11])
    #             left_opt_tcost   =  float(opt[12])
    #             right_opt_id     =  int(opt[13])
    #             right_opt_type   =  str(opt[14])
    #             rightt_opt_scost =  float(opt[15])
    #             right_opt_tcost  =  float(opt[16])
    #             db_sql_opt_costs[current_db][current_sql][str(opt[0])] += max(0.0, float(opt[2]) - max(left_opt_tcost, right_opt_tcost))

    # 依次遍历每个 SQL 语句的信息
    line_num = 0
    last_sql = ""
    ignore_opt = [] # 判断一些需要跳过的算子
    print("Processing Operator Vector.")
    for j_line, sql_opts, e_line in zip(j_lines, sql_operators, e_lines):
        line_num = line_num + 1
        current_sql = re.sub(r"[ \t]+", " ", str(e_line[0])).strip()
        current_db = str(e_line[1]).strip()
        if last_sql != current_sql:
            line_num = 1
            last_sql = current_sql

        if line_num == 1:
            for j in range(0, int((len(e_line)-2)/6)):
                expr_id         =   int(e_line[6*j+2])
                expr_count      =   int(e_line[6*j+3])
                expr_opt_id     =   int(e_line[6*j+4])
                expr_opt_type   =   str(e_line[6*j+5])
                expr_opt_scost  =   float(e_line[6*j+6])
                expr_opt_tcost  =   float(e_line[6*j+7])

                if expr_id not in eeop_count[current_db]:
                    print(f"Expression {expr_id} for {expr_opt_type} not in eeop_count!")
                    if expr_opt_id not in ignore_opt:
                        ignore_opt.append((expr_opt_id, expr_opt_type, expr_opt_scost, expr_opt_tcost))
                    continue

                for eeop in eeop_names:
                    opt_vectors[current_db][current_sql][expr_opt_id]["eeop_count"][eeop]   +=   eeop_count[current_db][expr_id][eeop] * expr_count
        elif line_num == 2:
            # 先预加载整个语句的所有算子，方便后面直接获取左右子树信息
            current_opts = {}
            current_opts[(0, 'T_Invalid', 0.0, 0.0)] = [0, 'T_Invalid', 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0, 'T_Invalid', 0.0, 0.0, 0, 'T_Invalid', 0.0, 0.0]
            for opt in sql_opts:
                opt_id = int(opt[0])
                opt_type = str(opt[1])
                opt_scost = float(opt[2])
                opt_tcost = float(opt[3])
                current_opts[(opt_id, opt_type, opt_scost, opt_tcost)] = opt
            # 逐个读取当前语句的算子
            for opt in sql_opts:
                opt_id          =   int(opt[0])
                opt_type        =   str(opt[1])
                opt_scost       =   float(opt[2])
                opt_tcost       =   float(opt[3])
                input_rows      =   int(opt[4])
                output_rows     =   int(opt[5])
                filter_rows     =   int(opt[6])
                opt_stime       =   float(opt[7])
                opt_ttime       =   float(opt[8])
                left_opt_id     =   int(opt[9])
                left_opt_type   =   str(opt[10])
                left_opt_scost  =   float(opt[11])
                left_opt_tcost  =   float(opt[12])
                right_opt_id    =   int(opt[13])
                right_opt_type  =   str(opt[14])
                right_opt_scost =   float(opt[15])
                right_opt_tcost =   float(opt[16])

                left_opt        =   current_opts[(left_opt_id, left_opt_type, left_opt_scost, left_opt_tcost)]
                right_opt       =   current_opts[(right_opt_id, right_opt_type, right_opt_scost, right_opt_tcost)]

                opt_vectors[current_db][current_sql][opt_id]["opt_id"]          =   opt_id
                opt_vectors[current_db][current_sql][opt_id]["opt_type"]        =   opt_type
                opt_vectors[current_db][current_sql][opt_id]["startup_cost"]    =   opt_scost
                opt_vectors[current_db][current_sql][opt_id]["total_cost"]      =   opt_tcost -max(float(left_opt[3]), float(right_opt[3]))
                # opt_vectors[current_db][current_sql][opt_id]["total_cost"]      =   opt_tcost
                opt_vectors[current_db][current_sql][opt_id]["startup_time"]    =   opt_stime
                opt_vectors[current_db][current_sql][opt_id]["total_time"]      =   opt_ttime - max(float(left_opt[8]), float(right_opt[8]))
                # opt_vectors[current_db][current_sql][opt_id]["total_time"]      =   opt_ttime
                opt_vectors[current_db][current_sql][opt_id]["output_rows"]     =   output_rows
                opt_vectors[current_db][current_sql][opt_id]["filtered_rows"]   =   filter_rows
                opt_vectors[current_db][current_sql][opt_id]["left_opt_id"]     =   left_opt_id
                opt_vectors[current_db][current_sql][opt_id]["left_opt_type"]   =   left_opt_type
                opt_vectors[current_db][current_sql][opt_id]["left_scost"]      =   left_opt_scost
                opt_vectors[current_db][current_sql][opt_id]["left_tcost"]      =   left_opt_tcost
                opt_vectors[current_db][current_sql][opt_id]["left_actual_rows"]      =   int(left_opt[5])
                opt_vectors[current_db][current_sql][opt_id]["left_total_time"]       =   float(left_opt[8])
                opt_vectors[current_db][current_sql][opt_id]["right_opt_id"]    =   right_opt_id
                opt_vectors[current_db][current_sql][opt_id]["right_opt_type"]  =   right_opt_type
                opt_vectors[current_db][current_sql][opt_id]["right_scost"]     =   right_opt_scost
                opt_vectors[current_db][current_sql][opt_id]["right_tcost"]     =   right_opt_tcost
                opt_vectors[current_db][current_sql][opt_id]["right_actual_rows"]     =   int(right_opt[5])
                opt_vectors[current_db][current_sql][opt_id]["right_total_time"]      =   float(right_opt[8])

                if "Join" in opt_type or "NestLoop" in opt_type:
                    opt_vectors[current_db][current_sql][opt_id]["input_rows"] = max(int(left_opt[5]), int(right_opt[5]))
                elif "Scan" in opt_type:
                    opt_vectors[current_db][current_sql][opt_id]["input_rows"] = input_rows  # output_rows + filter_rows
                else:
                    opt_vectors[current_db][current_sql][opt_id]["input_rows"] = input_rows + int(left_opt[5]) + int(right_opt[5])

                # no_expr_opt = True
                # for eeop in eeop_names:
                #     if int(opt_vectors[current_db][current_sql][opt_id]["eeop_count"][eeop]) != 0:
                #         no_expr_opt = False
                #         break
                # if no_expr_opt:
                #     continue

                with open(output_file_path, 'a+', newline='', encoding='gbk') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    row = {}
                    row["查询语句"] = current_sql
                    row["数据库名"] = current_db
                    row["算子编号"] = opt_vectors[current_db][current_sql][opt_id]["opt_id"]
                    row["算子类型"] = opt_vectors[current_db][current_sql][opt_id]["opt_type"]
                    row["启动Cost"] = opt_vectors[current_db][current_sql][opt_id]["startup_cost"]
                    row["总Cost"]   = opt_vectors[current_db][current_sql][opt_id]["total_cost"]
                    row["算子启动时间"] = opt_vectors[current_db][current_sql][opt_id]["startup_time"]
                    row["算子总时间"] = opt_vectors[current_db][current_sql][opt_id]["total_time"]
                    row["输入行数"] = opt_vectors[current_db][current_sql][opt_id]["input_rows"]
                    row["输出行数"] = opt_vectors[current_db][current_sql][opt_id]["output_rows"]
                    row["过滤行数"] = opt_vectors[current_db][current_sql][opt_id]["filtered_rows"]
                    row["左子树算子编号"] = opt_vectors[current_db][current_sql][opt_id]["left_opt_id"]
                    row["左子树类型"] = opt_vectors[current_db][current_sql][opt_id]["left_opt_type"]
                    row["左子树启动Cost"] = opt_vectors[current_db][current_sql][opt_id]["left_scost"]
                    row["左子树总Cost"] = opt_vectors[current_db][current_sql][opt_id]["left_tcost"]
                    row["左子树输出行数"] = opt_vectors[current_db][current_sql][opt_id]["left_actual_rows"]
                    row["左子树总时间"] = opt_vectors[current_db][current_sql][opt_id]["left_total_time"]
                    row["右子树算子编号"] = opt_vectors[current_db][current_sql][opt_id]["right_opt_id"]
                    row["右子树类型"] = opt_vectors[current_db][current_sql][opt_id]["right_opt_type"]
                    row["右子树启动Cost"] = opt_vectors[current_db][current_sql][opt_id]["right_scost"]
                    row["右子树总Cost"] = opt_vectors[current_db][current_sql][opt_id]["right_tcost"]
                    row["右子树输出行数"] = opt_vectors[current_db][current_sql][opt_id]["right_actual_rows"]
                    row["右子树总时间"] = opt_vectors[current_db][current_sql][opt_id]["right_total_time"]
                    # for opt in opt_list:
                    #     row[opt] = float(db_sql_opt_costs[current_db][current_sql][opt])
                    for eeop in eeop_names:
                        row[eeop] = int(opt_vectors[current_db][current_sql][opt_id]["eeop_count"][eeop])
                    writer.writerow(row)