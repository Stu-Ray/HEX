# -*- coding: gbk -*-

# 定义所有 TPCH 查询特征
QUERIES = {
    1: "select l_returnflag, l_linestatus, sum(l_quantity) as sum_qty",
    2: "select s_acctbal, s_name, n_name, p_partkey, p_mfgr, s_address, s_phone, s_comment",
    3: "select l_orderkey, sum(l_extendedprice * (1 - l_discount)) as revenue, o_orderdate",
    4: "select o_orderpriority, count(*) as order_count",
    5: "select n_name, sum(l_extendedprice * (1 - l_discount)) as revenue",
    6: "select sum(l_extendedprice * l_discount) as revenue",
    7: "select supp_nation, cust_nation, l_year, sum(volume) as revenue",
    8: "select o_year, sum(case when nation = 'BRAZIL' then volume else 0 end) / sum(volume) as mkt_share",
    9: "select nation, o_year, sum(amount) as sum_profit",
    10: "select c_custkey, c_name, sum(l_extendedprice * (1 - l_discount)) as revenue",
    11: "select ps_partkey, sum(ps_supplycost * ps_availqty) as value",
    12: "select l_shipmode, sum(case when o_orderpriority =",
    13: "select c_count, count(*) as custdist",
    14: "select 100.00 * sum(case when p_type like",
    15: ["create view revenue0 (supplier_no, total_revenue)", "select l_suppkey, sum(l_extendedprice * (1 - l_discount))"],
    16: "select p_brand, p_type, p_size, count(distinct ps_suppkey) as supplier_cnt",
    17: "select sum(l_extendedprice) / 7.0 as avg_yearly",
    18: "select c_name, c_custkey, o_orderkey, o_orderdate, o_totalprice",
    19: "select sum(l_extendedprice* (1 - l_discount)) as revenue",
    20: "select s_name, s_address from supplier",
    21: "select s_name, count(*) as numwait",
    22: "select cntrycode, count(*) as numcust"
}

# 定义 identify_query 函数
def identify_query(sql_query):
    for query_id, query in QUERIES.items():
        if isinstance(query, list):  # Query 15 特殊处理，包含多个子查询
            if any(sub_query in sql_query for sub_query in query):
                return query_id
        elif query in sql_query:
            return query_id
    return -1  # 未匹配任何查询

# 测试函数
if __name__ == "__main__":
    # 示例 SQL 查询
    id=identify_query("select cntrycode, count(*) as numcust")
    print(id)