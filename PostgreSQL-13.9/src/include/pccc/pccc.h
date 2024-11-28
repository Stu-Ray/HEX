/*-------------------------------------------------------------------------
 *
 * pccc.h
 *
 * src/include/pccc/pccc.h
 *
 *-------------------------------------------------------------------------*/

#ifndef PCCC_H
#define PCCC_H

#include <unistd.h>
#include <time.h>

#include "miscadmin.h"
#include "storage/lock.h"

/************************* #RAIN : PC3 TRANSACTION PREDICTION CACHE ************************/

typedef struct
{
  	Oid 		typeid;
  	Oid 		tableid;
  	Oid 		wid;
  	Oid 		did;
  	Oid 		cid;
  	Oid 		iid;
	Oid			otherid;
	long		hashValue;
} NewOrderSQLData;

typedef struct
{
	long				inputHash;
	size_t				inputSize;
	long				outputHash;
	size_t				outputSize;
    NewOrderSQLData 	workingset[MAX_ENTRIES];
	int					count;
} PC3HashKey;

/* ------------- About EWL ------------- */

typedef struct TransactionWorkingSet{
	VirtualTransactionId 						vxid;			
	PC3HashKey 									workingset;
	bool										committed;
	time_t										begin_time;
	time_t										commit_time;
	struct 		TransactionWorkingSet*	 		next;
} TransactionWorkingSet;

typedef struct TransactionPool{
	TransactionWorkingSet*		headNode;
	TransactionWorkingSet*		transactions[TXN_SIZE];
	LWLock						lock;
} TransactionPool;

/* ------------- About SSN ------------- */
typedef enum ConflictType
{
	Conf_WR,
	Conf_WW,					
	Conf_RW				
} ConflictType;

typedef struct InConflictRecord{
	VirtualTransactionId		source_vxid;
	ConflictType				type;
}InConflictRecord;


typedef struct OutConflictRecord{
	VirtualTransactionId		destination_vxid;
	ConflictType				type;
}OutConflictRecord;


typedef struct ConflictRecord{
	int						inCount;
	int						outCount;
	InConflictRecord		inConflicts[CONFLICT_SIZE];
	OutConflictRecord		outConflicts[CONFLICT_SIZE];
	time_t					maxInTime; 
	time_t					minOutTime;
}ConflictRecord;

typedef struct CommitTxn{
	VirtualTransactionId	vxid;
	bool					committed;
	time_t  				commitTime;
	ConflictRecord*			conflicts;
}CommitTxn;

typedef struct CommitTxnPool{
	CommitTxn* commitTxn[TXN_SIZE];
	LWLock	writeLock;
}CommitTxnPool;

#endif							/* PCCC_H */
