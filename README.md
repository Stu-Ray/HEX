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

## Installation

### LLVM

This implementation requires the appropriate LLVM version. Use the script `Scripts/install_llvm15.sh` to download and install llvm 15.0.7 for PostgreSQL 13.9: 

```shell
./install_llvm15.sh
```

### PostgreSQL

The modified source codes for PostgreSQL 13.9 has been uploaded in `Postgresql-13.9/`. Use the script `Scripts/install_pg_source.sh` to compile and install it. Remember to change the directory in the script according to your own environment.

```shell
./install_pg_source.sh
```

You can then initialize the database clusters and start the PG server in the installation directory:

```shell
cd $PG_INSTALL_DIR/bin

./initdb -D ../data

./pg_ctl -D ../data start
```

The modified PostgreSQL added a few configuration parameters as listed in `Postgresql-13.9/postgresql.conf`. Put it in the `PG_DATA` directory and change the corresponding configurations for different testing purposes. Every change requires the PG server to be restarted:

```shell
cd $PG_INSTALL_DIR/bin

./pg_ctl -D ../data restart
```

## Usage

Using the modified PostgreSQL, each query execution can generate related data files in the given directory, which can be analyzed using Python scripts and models in `DataAnalysis/`.

The workloads we use are TPC-H and Join-Order-Benchmark (JOB). The data and tools can be downloaded according to the README file in `Workloads/`.

The data and queries for JOB are provided in the repository in README file.

We provide a few scripts for generating data, importing data, creating databases and tables, as well as executing the generated queries for TPC-H in `Workloads/Scripts/TPC-H`.

