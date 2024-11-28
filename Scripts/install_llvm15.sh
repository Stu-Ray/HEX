#!/bin/bash

# 下载并安装LLVM 15.0.7，如果下载github代码过慢，可参考：https://blog.csdn.net/qq_20490175/article/details/136159452

# Ubuntu 20.0.4默认安装的llvm-config的位置：/usr/local/bin/llvm-config

wget https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.7/clang-15.0.7.src.tar.xz

wget https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.7/cmake-15.0.7.src.tar.xz

wget https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.7/llvm-15.0.7.src.tar.xz

tar -xf clang-15.0.7.src.tar.xz

tar -xf cmake-15.0.7.src.tar.xz

tar -xf llvm-15.0.7.src.tar.xz

mv llvm-15.0.7.src llvm

mv clang-15.0.7.src clang

mv clang llvm/tools/

cp cmake-15.0.7.src/Modules/* llvm/cmake/modules/

cd llvm

mkdir build

cd build

cmake ../ -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=MinSizeRel -DLLVM_INCLUDE_BENCHMARKS=OFF                 

make -j4 && make install