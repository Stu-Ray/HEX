/*-------------------------------------------------------------------------
 *
 * jit.c
 *	  Provider independent JIT infrastructure.
 *
 * Code related to loading JIT providers, redirecting calls into JIT providers
 * and error handling.  No code specific to a specific JIT implementation
 * should end up here.
 *
 *
 * Copyright (c) 2016-2020, PostgreSQL Global Development Group
 *
 * IDENTIFICATION
 *	  src/backend/jit/jit.c
 *
 *-------------------------------------------------------------------------
 */
#include "postgres.h"

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#include "executor/execExpr.h"
#include "fmgr.h"
#include "jit/jit.h"
#include "miscadmin.h"
#include "utils/fmgrprotos.h"
#include "utils/resowner_private.h"

#include "nodes/nodes.h"

/************************* #RAIN : PC3 ************************/
bool		ssn 		= 	false;
bool		s2pl 		= 	false;
bool 		boolPrint 	= 	false;

/* GUCs */
bool		jit_enabled = true;
char	   *jit_provider = NULL;
bool		jit_debugging_support = false;
bool		jit_dump_bitcode = false;
bool		jit_expressions = true;
bool		jit_profiling_support = false;
bool		jit_tuple_deforming = true;
double		jit_above_cost = 100000;
double		jit_inline_above_cost = 500000;
double		jit_optimize_above_cost = 500000;

static JitProviderCallbacks provider;
static bool provider_successfully_loaded = false;
static bool provider_failed_loading = false;


static bool provider_init(void);
static bool file_exists(const char *name);

/*
 * SQL level function returning whether JIT is available in the current
 * backend. Will attempt to load JIT provider if necessary.
 */
Datum
pg_jit_available(PG_FUNCTION_ARGS)
{
	PG_RETURN_BOOL(provider_init());
}


/*
 * Return whether a JIT provider has successfully been loaded, caching the
 * result.
 */
static bool
provider_init(void)
{
	char		path[MAXPGPATH];
	JitProviderInit init;

	/* don't even try to load if not enabled */
	if (!jit_enabled)
		return false;

	/*
	 * Don't retry loading after failing - attempting to load JIT provider
	 * isn't cheap.
	 */
	if (provider_failed_loading)
		return false;
	if (provider_successfully_loaded)
		return true;

	/*
	 * Check whether shared library exists. We do that check before actually
	 * attempting to load the shared library (via load_external_function()),
	 * because that'd error out in case the shlib isn't available.
	 */
	snprintf(path, MAXPGPATH, "%s/%s%s", pkglib_path, jit_provider, DLSUFFIX);
	elog(DEBUG1, "probing availability of JIT provider at %s", path);
	if (!file_exists(path))
	{
		elog(DEBUG1,
			 "provider not available, disabling JIT for current session");
		provider_failed_loading = true;
		return false;
	}

	/*
	 * If loading functions fails, signal failure. We do so because
	 * load_external_function() might error out despite the above check if
	 * e.g. the library's dependencies aren't installed. We want to signal
	 * ERROR in that case, so the user is notified, but we don't want to
	 * continually retry.
	 */
	provider_failed_loading = true;

	/* and initialize */
	init = (JitProviderInit)
		load_external_function(path, "_PG_jit_provider_init", true, NULL);
	init(&provider);

	provider_successfully_loaded = true;
	provider_failed_loading = false;

	elog(DEBUG1, "successfully loaded JIT provider in current session");

	return true;
}

/*
 * Reset JIT provider's error handling. This'll be called after an error has
 * been thrown and the main-loop has re-established control.
 */
void
jit_reset_after_error(void)
{
	if (provider_successfully_loaded)
		provider.reset_after_error();
}

/*
 * Release resources required by one JIT context.
 */
void
jit_release_context(JitContext *context)
{
	if (provider_successfully_loaded)
		provider.release_context(context);

	ResourceOwnerForgetJIT(context->resowner, PointerGetDatum(context));
	pfree(context);
}


/*
 * Ask provider to JIT compile an expression.
 *
 * Returns true if successful, false if not.
 */
bool
jit_compile_expr(struct ExprState *state)
{
	/*
	 * We can easily create a one-off context for functions without an
	 * associated PlanState (and thus EState). But because there's no executor
	 * shutdown callback that could deallocate the created function, they'd
	 * live to the end of the transactions, where they'd be cleaned up by the
	 * resowner machinery. That can lead to a noticeable amount of memory
	 * usage, and worse, trigger some quadratic behaviour in gdb. Therefore,
	 * at least for now, don't create a JITed function in those circumstances.
	 */
	if (!state->parent)
		return false;

	// -------------------------------------- #RAIN -------------------------------------- 
	
	if(enableME && containExpr)
	{
		state->parent->jit_level 	= 	0;

		int		steps_length	=	state->steps_len; 

		int*	eeop_steps		=	(int*)palloc((steps_length + 1) * sizeof(int));

		int		opt_id			=	0;
		int		opt_type		=	0;
		double	opt_scost		=	0.0;
		double	opt_tcost		=	0.0;

		if(state->parent->plan)
		{
			opt_id		=	(int)state->parent->plan->plan_node_id;
			opt_type	=	(int)state->parent->plan->type;
			opt_scost	=	(double)state->parent->plan->startup_cost;
			opt_tcost 	=	(double)state->parent->plan->total_cost;
		}

		for(int i = 0; i < steps_length; i++)
		{
			ExprEvalOp real_opcode = ExecEvalStepOp(state, &state->steps[i]);

			eeop_steps[i]	=	(int)real_opcode;
		}

		ExprSteps*	current_expr	=	add_expression(steps_length, eeop_steps);

		if(current_expr)
		{
			int 	expressionId 	=	current_expr->expression_id;

			long long eHash = calculate_hash(steps_length, eeop_steps);

			// OperatorInfo* opt = findOperatorInfo(opt_id, opt_type, opt_scost, opt_tcost);

			if(state->parent->plan)
			{
				bool found_expr_info = false;

				int expr_info_index = 0;

				while(expr_info_index < allExprInfoNum)
				{
					if(currentSQLExprs[expr_info_index].hash == eHash && currentSQLExprs[expr_info_index].step_lens == steps_length)
					{
						if(currentSQLExprs[expr_info_index].op)
						{
							if(currentSQLExprs[expr_info_index].op->type == opt_type && currentSQLExprs[expr_info_index].op->startup_cost == opt_scost && 
								currentSQLExprs[expr_info_index].op->total_cost == opt_tcost && currentSQLExprs[expr_info_index].op->optId == opt_id)
							{
								found_expr_info	= true;
								break;
							}
						}
						else if(opt_type == 0)
						{
							found_expr_info	= true;
							break;
						}	
					}

					expr_info_index++;
				}

				if(!found_expr_info)
				{
					currentSQLExprs[expr_info_index].hash            =   	eHash;
					currentSQLExprs[expr_info_index].step_lens       =   	steps_length;
					currentSQLExprs[expr_info_index].count           =   	0L;

					for(int i=0; i<steps_length; i++)
					{   
						currentSQLExprs[expr_info_index].steps[i] = eeop_steps[i];
					}

					currentSQLExprs[expr_info_index].next      	=   NULL;

					if(expr_info_index > 0)
						currentSQLExprs[expr_info_index-1].next = &currentSQLExprs[expr_info_index];

					currentSQLExprs[expr_info_index].op			= 	findOperatorInfo(opt_id, opt_type, opt_scost, opt_tcost);
					
					currentSQLExprs[expr_info_index].expression_id   =	expressionId;

					allExprInfoNum++;
				}

				bool 	allowJIT		=	true;

			
				bool 	found_expr		=	false;

				for(int j = 0; j < currentExprNum; j++)
				{
					if(currentExprList[j].expression_id	==	expressionId && currentExprList[j].hash == eHash && currentExprList[j].step_lens == steps_length)
					{
						if(currentExprList[j].op)
						{
							if(currentExprList[j].op->type == opt_type && currentExprList[j].op->startup_cost == opt_scost && currentExprList[j].op->total_cost == opt_tcost && currentExprList[j].op->optId == opt_id)
							{
								found_expr	=	true;
								state->parent->list_index 	= 	j;
								break;
							}
						}
						else if(opt_id == 0 && opt_type == 0)
						{
							found_expr	=	true;
							state->parent->list_index 	= 	j;
							break;
						}
					}
				}

				if(!found_expr)
				{
					state->parent->list_index 						= 	currentExprNum;
					currentExprList[currentExprNum].expression_id	=	expressionId;
					currentExprList[currentExprNum].hash			=	eHash;
					currentExprList[currentExprNum].step_lens		=	steps_length;
					currentExprList[currentExprNum].op				=	findOperatorInfo(opt_id, opt_type, opt_scost, opt_tcost);
					if(!testME)
						currentExprJITLevels[currentExprNum++]			=	0;
					else
						currentExprNum++;
				}
				
				int eIndex	=	state->parent->list_index;
					
				int	current_jit_level	=	currentExprJITLevels[eIndex];

				state->parent->jit_level	=	current_jit_level;

				if(current_jit_level	==	0)
				{
					allowJIT	=	false;
				}
				else
				{
					jit_enabled	=	true;

					state->parent->state->es_jit_flags |=	PGJIT_PERFORM | PGJIT_EXPR;

					if(current_jit_level >= 2)
					{
						state->parent->state->es_jit_flags |= PGJIT_INLINE;
					}

					if(current_jit_level == 3)
					{
						state->parent->state->es_jit_flags |= PGJIT_OPT3;
					}
				}

				printf("[Current Expr] ID = %d, jit_level = %d\n", expressionId, state->parent->jit_level);
					
				if(printEEOP)
				{
					for(int i = 0; i < steps_length; i++)
					{
						printf("	%s (%d)\n", getExprEvalOpName((ExprEvalOp)eeop_steps[i]), eeop_steps[i]);
					} 
				}
				
				if(printExprLevels)
				{
					const char* filename = "/data/jit.csv";

					FILE *jit_file = fopen(filename, "a+"); 

					fprintf(jit_file, "%d,%d,%d,%s,%.6lf,%.6lf,", expressionId, state->parent->jit_level, opt_id, getNodeTagName((NodeTag)opt_type), opt_scost, opt_tcost);

					fclose(jit_file);
				}

				if(!allowJIT)
				{
					return false;
				}
			}
		}
	}
	
	// -------------------------------------- #RAIN -------------------------------------- 

	/* if no jitting should be performed at all */
	if (!(state->parent->state->es_jit_flags & PGJIT_PERFORM))
		return false;

	/* or if expressions aren't JITed */
	if (!(state->parent->state->es_jit_flags & PGJIT_EXPR))
		return false;

	/* this also takes !jit_enabled into account */
	if (provider_init())
		return provider.compile_expr(state);

	return false;
}

/* Aggregate JIT instrumentation information */
void
InstrJitAgg(JitInstrumentation *dst, JitInstrumentation *add)
{
	dst->created_functions += add->created_functions;
	INSTR_TIME_ADD(dst->generation_counter, add->generation_counter);
	INSTR_TIME_ADD(dst->inlining_counter, add->inlining_counter);
	INSTR_TIME_ADD(dst->optimization_counter, add->optimization_counter);
	INSTR_TIME_ADD(dst->emission_counter, add->emission_counter);
}

static bool
file_exists(const char *name)
{
	struct stat st;

	AssertArg(name != NULL);

	if (stat(name, &st) == 0)
		return S_ISDIR(st.st_mode) ? false : true;
	else if (!(errno == ENOENT || errno == ENOTDIR))
		ereport(ERROR,
				(errcode_for_file_access(),
				 errmsg("could not access file \"%s\": %m", name)));

	return false;
}
