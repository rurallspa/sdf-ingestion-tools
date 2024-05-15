# sdf-tag-telemetries

## Ingestione automatica telemetrie degli implement

Questo script serve per:
1. Convertire telemetrie degli implement da csv a json (*base64-encoded*)
2. Mandare in ingestione file json (base64-encoded) tramite direct put su AWS Firehose, al delivery stream `sdf-implement-tag-telemetries`

## Requirements
- numpy==1.21.5
- pandas==2.2.2

## Utilizzo
Dopo aver copiato i file .csv delle telemetrie nella rispettiva cartella **csv**, per completare sia la conversione che l'ingestione è sufficiente eseguire i seguenti comandi in sequenza:

0. `pip install -r requirements.txt`
1. `bash reset-folders.sh` (**opzionale**)
2. `python3 convert-csv.py`
3. `bash put-records-batch.sh` **oppure** `bash put-records.sh`

Il comando `bash reset-folders.sh`, eseguito opzionalmente all'inizio della pipeline, permette di svuotare rapidamente le cartelle **json**, **base64** e **base64-batch**, popolate dallo script `convert-csv.py` ed utilizzate in seguito come base per l'ingestione.  

Lo script `convert-csv.py`, nel dettaglio, carica tutti i file .csv contenuti nella cartella **csv**, li converte nei 2 formati desiderati (*json* e *base64*) e li salva nelle rispettive cartelle sotto forma di singolo file per telemetria. Allo scopo di implementare l'ingestione batch, inoltre, le telemetrie *base64* encoded vengono anche aggregate in liste di max 500 elementi e 4 MB, come da [specifiche del comando put-records-batch](https://docs.aws.amazon.com/cli/latest/reference/firehose/put-record-batch.html). Questi file vengono dunque salvati nella cartella **base64-batch**.

Utilizzando infine il comando `bash put-records-batch.sh` lo script manderà su AWS Firehose al massimo 500 file alla volta, prendendoli dalla cartella **base64-batch** dove sono stati in precedenza aggregati e cancellandoli man mano. Utilizzando, invece, `bash put-records.sh`, lo script eseguirà un comando per ogni file precedentemente creato nella cartella **base64**, anche in questo caso eliminando il rispettivo *json* dopo aver completato ogni `put-record`.  

**NB: Eseguire entrambi i comandi `bash put-records-batch.sh` e `bash put-records.sh` causerà un'ingestione duplicata degli stessi file. A tale proposito, è consigliato eseguire nuovamente il comando `bash reset-folders.sh` al termine dell'operazione di ingestione**.