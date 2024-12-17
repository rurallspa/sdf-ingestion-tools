# sdf-ingestion-tools

## Utilizzo

Per utilizzare gli script contenuti in questa repository, è necessario eseguire i seguenti step preliminari:

```sh
git clone https://github.com/rurallspa/sdf-ingestion-tools.git
cd sdf-ingestion-tools
pip install -r requirements.txt
```

## Conversione telemetrie da CSV a JSON

Per convertire telemetrie da CSV a JSON, è necessario copiare i file CSV all'interno della cartella `telemetries-to-convert`.  
I file devono rispettare i seguenti requisiti:
- Per ogni set di telemetrie, devono essere inclusi due file distinti per i parametri e per la posizione GPS.
- Ogni coppia di file deve essere riferita a un unico VIN.
- Il nome dei file deve seguire il seguente schema:
    - `<VIN>_telemetry_param.csv` **per il file contenente i valori dei parametri**
    - `<VIN>_telemetry_position.csv` **per il file contenente i valori delle posizioni GPS**
  
Nella cartella sono inclusi alcuni esempi che possono essere usati come riferimento.  
  
Dopo aver copiato i file correttamente rinominati, è sufficente eseguire il comando:
```sh
python3 convert_telemetries.py
```
per generare un file JSON univoco per ogni telemetria, pronto per essere ingerito su S3. L'output viene salvato nella cartella `telemetries`.

## Ingestione automatica telemetrie

Questo script serve per mandare in ingestione files json di telemetrie. Per fare ciò è possibile seguire due strade:

1. Publish Bulk via SNS, che permette di inviare un massimo 10 telemetrie per messaggio al topic SNS `sdf-ingestion`;
2. Put Records Batch via Firehose, che permette di inviare un massimo di 500 telemetrie per messaggio direttamente allo stream Firehose `SDF-ingestion`.

### Publish Bulk via SNS
Per caricare le telemetrie in formato JSON contenute nella directory **telemetries** è sufficiente eseguire il comando:  

`bash publishbulk.sh`

lo script manderà al massimo 10 file alla volta, cancellandoli dalla cartella **telemetries** (se il publish avrà successo), su SNS al topic `"arn:aws:sns:eu-west-1:902738125373:sdf-ingestion"`. 

**NB: Di default, `aws` utilizzerà il profilo aws chiamato "rurall"**

### Put Records Batch via Firehose
Per caricare le telemetrie in formato JSON contenute nella directory **telemetries** è necessario eseguire i seguenti comandi:

```sh
python3 make_telemetries_batch.py telemetries
bash put-records-batch-telemetries.sh
```

Il primo script (`make_telemetries_batch.py`) aggregherà le singole telemetrie in formato JSON contenute nella directory specificata (i.e. **telemetries**) in batch di massimo 500 messaggi e 4 MB l'uno (limiti imposti da AWS per put-records-batch). I batch, in formato JSON, vengono salvati nella output directory **telemetries-batch**. I file originali vengono spostati dalla input directory specificata alla directory di backup (i.e. **telemetries_processed**).  

Il secondo script (`put-records-batch-telemetries.sh`) si occuperà di inviare i batch, eliminandoli dalla input directory **telemetries-batch**, su Firehose allo stream `SDF-ingestion`. 

**NB: caricare un numero elevato di telemetrie "sparse" (i.e.: tante coppie VIN-data distinte)** con direct put di Firehose potrebbe portare a sforare il limite di partizioni aperte (500). Se questo dovesse succedere, è opportuno procedere a recuperare i dati per cui l'ingestione è fallita con il metodo indicato nella sezione successiva.  

Un'altra soluzione potrebbe essere aumentare lo sleep fra un batch e l'altro, specificato dentro il loop nello script `put-records-batch-telemetries.sh` (attualmente 2 secondi).

## Recupero telemetrie dagli errori di FIREHOSE

Nel caso di fossero degli errori durante l'ingestione è possibile raccogliere i file e ridirigerli in ingestione.
Per facilitare l'operazione, sono stati creati due step di script.
Il primo script scaricherà i files da s3, mettendoli nella cartella **files**:

`bash get-telemetries_step1.sh format-conversion-failed`

scaricherà i files della cartella *format-conversion-failed* dal percorso `s3://rurall-sdf-ingestion/errors/` e li metterà in un'unica cartella **files/**. Questi file conterranno, uno per riga, dei dati JSON.

Il secondo script prende ognuno dei dati JSON di ogni file in **files/** e ne creerà un file .json con nome arbitrario in telemetries. Sarà poi possibile usare gli script indicati nella sezione precedente per procedere all'ingestione.
