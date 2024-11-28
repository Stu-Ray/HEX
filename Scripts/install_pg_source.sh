postgresql_dir="/opt/pg/pgsql"

llvm_config_dir="/opt/llvm/llvm-project-llvmorg-15.0.7/bin/llvm-config"

cd "$postgresql_dir"

make clean

./configure --prefix=`pwd`/debug --with-llvm LLVM_CONFIG="$llvm_config_dir" --enable-debug

make -j4 && make install