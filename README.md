# HEX: Expression-Aware Adaptive Hybrid Execution for Analytical Databases (ICDE 2025)
**HEX** is an expression-aware adaptive **H**ybrid **EX**ecution method for analytical databases. This is the official implementation of the paper "HEX: Expression-Aware Adaptive Hybrid Execution for Analytical Databases".

## Summary

<img src="https://my-typora-image-host.oss-cn-hangzhou.aliyuncs.com//img/image-20241128164954638.png" alt="image-20241128164954638" style="zoom: 50%;" /> 

Conventional database compilation execution mostly conduct optimization on the whole SQL query level. HEX, instead, applies a new strategy to deal with expression-level optimization. 

The artical describes several compilation execution strategies to compete in decision accuracy and query-execution performance in the database for OLAP tasks.

The experimental results indicate that:

- **PostgreSQL** strategy, whose original expert decision-makeing is a well-performed baseline, widely used as a standard to make optimization decisions according to the overall query costs.
- **Quartet**, a learning-based execution decision model for databases, further incorporates operator information into its end-to-end learning framework for query compilation decisions. The decision accuracy of Quartet approaches is significantly lower compared to PostgreSQL in some cases.
- **HEX** represents a transformative approach, optimizing in currently the smallest decision unit (expressions) in the database compilation executor:
  - **Benchmarking**: In comparisons of decision accuracy, HEX outperformed all the above algorithms across datasets ranging from 0.1GB to 10.0GB.
  - **Performance evaluation**: HEX demonstrated an average performance improvement of approximately 29% compared to PostgreSQL's expert decision execution mode in TPC-H workload of 1GB to 10GB, with a maximum improvement of around 55%.
  - **Generalization ability**: Tests on the JOB dataset indicate that HEX exhibits strong generalization capabilities.

## Environments

### LLVM

This implementation requires the appropriate LLVM version. Use the script `Scripts/install_llvm15.sh` to download and install LLVM 15.0.7 for PostgreSQL 13.9: 

```shell
./install_llvm15.sh
```

### PostgreSQL

The modified source codes for PostgreSQL 13.9 has been uploaded in `Postgresql-13.9/`. Use the script `Scripts/install_pg_source.sh` to compile and install it. Remember to change the directory in the script according to your own environment.

```shell
./install_pg_source.sh
```

You can then initialize the database cluster and start the PG server in the installation directory:

```shell
cd $PG_INSTALL_DIR/bin  # $PG_INSTALL_DIR refers to where PostgreSQL is installed

./initdb -D ../data

./pg_ctl -D ../data start
```

The modified PostgreSQL added a few configuration parameters as listed in `Postgresql-13.9/postgresql.conf`. Put it in the `PG_DATA` directory and change the corresponding configurations for different testing purposes. Every change requires the PG server to be restarted:

```shell
cd $PG_INSTALL_DIR/bin

./pg_ctl -D ../data restart
```

### Workloads

We conducted experiments on the workloads of **TPC-H** and **Join-Order-Benchmark (JOB)**.

The download links are here below:

- TPC-H: [TPC Current Specs](https://www.tpc.org/tpc_documents_current_versions/current_specifications5.asp)
- JOB: [gregrahn/join-order-benchmark: Join Order Benchmark (JOB)](https://github.com/gregrahn/join-order-benchmark)

### Baselines

Our experiments compares the HEX method with:

- PostgreSQL: the original expert decision making strategy decides the overall optimization level depending on the total cost of the whole plan tree. 
- [Quartet](https://codeocean.com/capsule/9528169/tree/v1): a learning-based strategy which can wisely predict the best overall optimization level depending on the cost of each operator in the plan tree. This method is proposed in the article *[Quartet: A Query Aware Database Adaptive Compilation Decision System](https://www.sciencedirect.com/science/article/abs/pii/S0957417423033432)*.

## Usage

Using the modified PostgreSQL, each query execution can generate related data files in the given directory (in ``/data/`` by default), which can be analyzed using Python scripts and models in `DataAnalysis/HEX/`. The data files which can be analyzed include:

- `report.csv`: one line for one statement, including expression count and the related operator.
- `jit.csv`: one line for one statement, including all the expression ids and their jit levels.
- `operator.csv`: one line for one operator with different statements seperated with empty lines, including all the operator information.
- `time.csv`: one line for one statement, including all the time information——generation time, inlining time, optimization time, emission time, compilation time, plan time, execution time.
- `expr_eeops.txt`: one line for one expression, including all the expression ids and the coresponding EEOPs.

Put the files in `DataAnalysis/HEX/Data/`, change the directory in Python script and you can analyze the information and generate the coresponding vector file for training models.

For generating the above files, use the configuration file `Postgresql-13.9/postgresql.conf` to overwrite the original .conf file in `PG_DATA` and then restart the server:

```shell
cp $PG_DATA/postgresql.conf $PG_DATA/postgresql.conf.bak	# $PG_DATA refers to where the database cluster is

mv $PG_ROOT/postgresql.conf $PG_DATA/postgresql.conf    # $PG_ROOT refers to the Postgresql-13.9/ in this repository

cd $PG_INSTALL_DIR/bin

./pg_ctl -D ../data restart
```

---

As for testing on the workloads, the data and queries for JOB are provided in the repository above. 

We provide a few scripts for generating data, importing data, creating databases and tables, as well as executing the generated queries for TPC-H in `Workloads/Scripts/TPC-H`. 

There are three scripts for executing TPC-H queries, serving for different purposes:

- `executeN.sh`: Execute the given query at the given database for the given times. Require 3 params:
  - X: The number of the SQL file (1-22, e.g., for pgX.sql)
  - N: The number of times to repeat the content
  - database_name: The name of the PostgreSQL database
- `executeAllN.sh`: Execute all the queries (1-22) at all the databases (100 MB-10 GB by default) for the given times. Require 1 param:
  - N: The number of times to repeat the content
- `executeAll.sh`: Execute all the queries (1-22) at all the databases (100MB-10GB by default) for the given times. Different execution number for different queries (pre-set in the script). No param required.

For example, If you want to execute every TPC-H query for 3 times in all the databases (100MB-10GB by default) PostgreSQL, you could executed the script like:

```shell
cd SCRIPT_PATH/tpch_queires

./executeAllN.sh 3 >> /data/output.txt   # output.txt is for recording the executing process and avoid printing it on terminal.
```

For testing all the queries for 4n times as said in the article, you can use the script `executeN.sh` to set the number of execution for every query.

---

