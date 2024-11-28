The three scripts for executing TPC-H queries serve for different purposes:

- executeN.sh: Execute the given query at the given database for the given times. Require 3 params:
  - X: The number of the SQL file (1-22, e.g., for pgX.sql)
  - N: The number of times to repeat the content
  - database_name: The name of the PostgreSQL database
- executeAllN.sh: Execute all the queries (1-22) at all the databases (100 MB-10 GB) for the given times. Require 1 param:
  - N: The number of times to repeat the content
- executeAll.sh: Execute all the queries (1-22) at all the databases (100MB-10GB) for the given times. Different execution number for different queries (pre-set in the script). No param required.
