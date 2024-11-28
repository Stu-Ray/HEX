-- 创建索引：Customer 表
CREATE UNIQUE INDEX idx_customer_custkey ON customer (c_custkey);
CREATE INDEX idx_customer_nationkey ON customer (c_nationkey);

-- 创建索引：Orders 表
CREATE UNIQUE INDEX idx_orders_orderkey ON orders (o_orderkey);
CREATE INDEX idx_orders_custkey ON orders (o_custkey);
CREATE INDEX idx_orders_orderdate ON orders (o_orderdate);

-- 创建索引：Lineitem 表
CREATE UNIQUE INDEX idx_lineitem_linenumber ON lineitem (l_orderkey, l_linenumber);
CREATE INDEX idx_lineitem_orderkey ON lineitem (l_orderkey);
CREATE INDEX idx_lineitem_partkey ON lineitem (l_partkey);
CREATE INDEX idx_lineitem_suppkey ON lineitem (l_suppkey);
CREATE INDEX idx_lineitem_shipdate ON lineitem (l_shipdate);
CREATE INDEX idx_lineitem_commitdate ON lineitem (l_commitdate);
CREATE INDEX idx_lineitem_receiptdate ON lineitem (l_receiptdate);

-- 可选组合索引，用于优化复杂查询
CREATE INDEX idx_lineitem_shipdate_orderkey ON lineitem (l_shipdate, l_orderkey);

-- 创建索引：Part 表
CREATE UNIQUE INDEX idx_part_partkey ON part (p_partkey);
CREATE INDEX idx_part_name ON part (p_name);

-- 创建索引：Supplier 表
CREATE UNIQUE INDEX idx_supplier_suppkey ON supplier (s_suppkey);
CREATE INDEX idx_supplier_nationkey ON supplier (s_nationkey);

-- 创建索引：Partsupp 表
CREATE UNIQUE INDEX idx_partsupp ON partsupp (ps_partkey, ps_suppkey);
CREATE INDEX idx_partsupp_partkey ON partsupp (ps_partkey);
CREATE INDEX idx_partsupp_suppkey ON partsupp (ps_suppkey);

-- 创建索引：Nation 表
CREATE UNIQUE INDEX idx_nation_nationkey ON nation (n_nationkey);
CREATE INDEX idx_nation_regionkey ON nation (n_regionkey);

-- 创建索引：Region 表
CREATE UNIQUE INDEX idx_region_regionkey ON region (r_regionkey);

