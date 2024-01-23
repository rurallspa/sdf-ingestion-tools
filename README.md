# sdf-ingestion-tools

## ingestione automatica telemetrie

Questo script serve per mandare in ingestione files json di telemetrie. Per fare ciò è sufficiente eseguire:

`bash publishbulk.sh`

avendo cura di avere una directory chiamata **telemetries** nella stessa cartella dello script. `publishbulk.sh` necessita inoltre di `helper.py` nella stessa directory.

lo script manderà al massimo 10 file alla volta, cancellandoli dalla cartella **telemetries** (se il publish avrà successo), su SNS al topic `"arn:aws:sns:eu-west-1:902738125373:sdf-ingestion"`. 

**NB: Di default, `aws` utilizzerà il profilo aws chiamato "rurall"**

## recupero telemetrie dagli errori di FIREHOSE

Nel caso di fossero degli errori durante l'ingestione è possibile raccogliere i file e ridirigerli in ingestione.
Per facilitare l'operazione, sono stati creati due step di script.
Il primo script scaricherà i files da s3, mettendoli nella cartella **files**:

`bash get-telemetries.step1.sh format-conversion-failed`

scaricherà i files della cartella *format-conversion-failed* dal percorso `s3://rurall-sdf-ingestion/errors/` e li metterà in un'unica cartella **files/**. Questi file conterranno, uno per riga, dei dati JSON.

Il secondo script prende ognuno dei dati JSON di ogni file in **files/** e ne creerà un file .json con nome arbitrario in telemetries. Sarà poi possibile usare `publishbulk.sh` per ripetere l'ingestione.
