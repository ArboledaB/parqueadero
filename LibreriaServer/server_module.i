%module(threads="1") server_module

%{
#include "server_module.h"
%}

%include "std_string.i"
%include "server_module.h"