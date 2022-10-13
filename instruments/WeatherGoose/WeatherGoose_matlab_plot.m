clear;
data = readtable('datalog_20221012.csv');



figure(1);clf;hold on;box on;
plot(data.date_time,data.ExpTable_Temperature_C_,'LineWidth',1.5);
plot(data.date_time,data.ExpTableAir_Temperature_C_,'LineWidth',1.5);
plot(data.date_time,data.NaTable_Temperature_C_,'LineWidth',1.5);
plot(data.date_time,data.KTable_Temperature_C_,'LineWidth',1.5);



ylabel('degree C');
title('Weather Goose data');
legend('Experiment table','Experiment air','Na table','K table');

