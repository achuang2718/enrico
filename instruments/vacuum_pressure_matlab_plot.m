clear all;
data = readtable('Vacuum_Log.csv');

Na_oven_change_date = datetime({'0022-02-03 09:00:00',...
                       '0022-04-13 09:00:00',...
                       '0022-06-06 09:00:00'});

% filter out data when Na oven ion pump is off during oven change
data.NA_OVEN_PUMPPressure(data.NA_OVEN_PUMPPressure == 9.9e9) = nan;

figure(3);clf;
semilogy(data.Time,data.MAIN_1__AND_NA_INTERMEDIATE_2__PumpPressure1);
for idx = 1:length(Na_oven_change_date)
    xline(Na_oven_change_date(idx));
end

ylim([1e-11,1e-9]);
ylabel('torr');
title('main ion pump pressure');
legend('main ion pump pressure','Na oven change date');

figure(1);clf;
semilogy(data.Time,data.NA_OVEN_PUMPPressure);
for idx = 1:length(Na_oven_change_date)
    xline(Na_oven_change_date(idx));
end

ylim([1e-11,5e-6]);
ylabel('torr');
title('Na oven chamber ion pump pressure');
legend('Na oven ion pump pressure','Na oven change date');

figure(2);clf;
semilogy(data.Time,data.K_OVEN_PUMPPressure);
for idx = 1:length(Na_oven_change_date)
    xline(Na_oven_change_date(idx));
end

ylim([1e-7,5e-6]);
ylabel('torr');
title('K oven chamber ion pump pressure');
