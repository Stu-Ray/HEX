#!/bin/bash

# Create the databases and tables, including. Require $postgresql_dir and the create_tpch_index.sql (below) directory pre-set.

# PG安装目录（非源码）
postgresql_dir="/opt/pg/pgsql/debug"

# 开始建表
start_scale=1.00  # 起始scale(GB)
step_scale=1.00   # 每次增加(GB)
end_scale=10.00    # 终止scale(GB)

# 起始数据
current_scale=$start_scale

cd "${postgresql_dir}/bin"

while (( $(echo "$current_scale <= $end_scale" | bc -l) )); do
    # 获取scale的个位、十分位、百分位
    integer_part=$(echo "scale=0; $current_scale/1" | bc)  # 获取整数部分，作为个位
    decimal_part=$(printf "%.2f" "$current_scale" | cut -d '.' -f 2)  # 获取两位小数部分

    # 分别提取十分位和百分位
    tens_digit=$(echo $decimal_part | cut -c 1)  # 十分位
    hundred_digit=$(echo $decimal_part | cut -c 2)  # 百分位

    # 格式化数据库名称，例如：TPCH_0_5_5，TPCH_1_0_0
    db_name="tpch_${integer_part}_${tens_digit}_${hundred_digit}"

    echo "Creating database $db_name..."
    
    psql -d postgres -c "CREATE DATABASE $db_name;"

    psql -d $db_name -c "
    CREATE TABLE NATION  (
        N_NATIONKEY  INTEGER NOT NULL,
        N_NAME       CHAR(25) NOT NULL,
        N_REGIONKEY  INTEGER NOT NULL,
        N_COMMENT    VARCHAR(152)
    );

    CREATE TABLE REGION  (
        R_REGIONKEY  INTEGER NOT NULL,
        R_NAME       CHAR(25) NOT NULL,
        R_COMMENT    VARCHAR(152)
    );

    CREATE TABLE PART  (
        P_PARTKEY     INTEGER NOT NULL,
        P_NAME        VARCHAR(55) NOT NULL,
        P_MFGR        CHAR(25) NOT NULL,
        P_BRAND       CHAR(10) NOT NULL,
        P_TYPE        VARCHAR(25) NOT NULL,
        P_SIZE        INTEGER NOT NULL,
        P_CONTAINER   CHAR(10) NOT NULL,
        P_RETAILPRICE DECIMAL(15,2) NOT NULL,
        P_COMMENT     VARCHAR(23) NOT NULL
    );

    CREATE TABLE SUPPLIER (
        S_SUPPKEY     INTEGER NOT NULL,
        S_NAME        CHAR(25) NOT NULL,
        S_ADDRESS     VARCHAR(40) NOT NULL,
        S_NATIONKEY   INTEGER NOT NULL,
        S_PHONE       CHAR(15) NOT NULL,
        S_ACCTBAL     DECIMAL(15,2) NOT NULL,
        S_COMMENT     VARCHAR(101) NOT NULL
    );

    CREATE TABLE PARTSUPP (
        PS_PARTKEY     INTEGER NOT NULL,
        PS_SUPPKEY     INTEGER NOT NULL,
        PS_AVAILQTY    INTEGER NOT NULL,
        PS_SUPPLYCOST  DECIMAL(15,2)  NOT NULL,
        PS_COMMENT     VARCHAR(199) NOT NULL
    );

    CREATE TABLE CUSTOMER (
        C_CUSTKEY     INTEGER NOT NULL,
        C_NAME        VARCHAR(25) NOT NULL,
        C_ADDRESS     VARCHAR(40) NOT NULL,
        C_NATIONKEY   INTEGER NOT NULL,
        C_PHONE       CHAR(15) NOT NULL,
        C_ACCTBAL     DECIMAL(15,2)   NOT NULL,
        C_MKTSEGMENT  CHAR(10) NOT NULL,
        C_COMMENT     VARCHAR(117) NOT NULL
    );

    CREATE TABLE ORDERS  (
        O_ORDERKEY       INTEGER NOT NULL,
        O_CUSTKEY        INTEGER NOT NULL,
        O_ORDERSTATUS    CHAR(1) NOT NULL,
        O_TOTALPRICE     DECIMAL(15,2) NOT NULL,
        O_ORDERDATE      DATE NOT NULL,
        O_ORDERPRIORITY  CHAR(15) NOT NULL,  
        O_CLERK          CHAR(15) NOT NULL,
        O_SHIPPRIORITY   INTEGER NOT NULL,
        O_COMMENT        VARCHAR(79) NOT NULL
    );

    CREATE TABLE LINEITEM (
        L_ORDERKEY    INTEGER NOT NULL,
        L_PARTKEY     INTEGER NOT NULL,
        L_SUPPKEY     INTEGER NOT NULL,
        L_LINENUMBER  INTEGER NOT NULL,
        L_QUANTITY    DECIMAL(15,2) NOT NULL,
        L_EXTENDEDPRICE  DECIMAL(15,2) NOT NULL,
        L_DISCOUNT    DECIMAL(15,2) NOT NULL,
        L_TAX         DECIMAL(15,2) NOT NULL,
        L_RETURNFLAG  CHAR(1) NOT NULL,
        L_LINESTATUS  CHAR(1) NOT NULL,
        L_SHIPDATE    DATE NOT NULL,
        L_COMMITDATE  DATE NOT NULL,
        L_RECEIPTDATE DATE NOT NULL,
        L_SHIPINSTRUCT CHAR(25) NOT NULL,
        L_SHIPMODE     CHAR(10) NOT NULL,
        L_COMMENT      VARCHAR(44) NOT NULL
    );
    "

    psql -d $db_name -f /opt/pg/pgsql/debug/bin/create_tpch_index.sql
    
    # 递增更新scale值
    current_scale=$(echo "$current_scale + $step_scale" | bc)
done