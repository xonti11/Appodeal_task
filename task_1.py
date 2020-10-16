import pandas as pd
import numpy as np
import os
pd.set_option("max_rows",100)

# функция определения инцидента - выход значения за пределы, определенного по правилу трех сигм
def get_incident(data,column_name):
    # определяем среднее и стандартное отклонение по дата центру, месяцу и часу
    group_data = data.groupby(['DC', 'h', 'm'])[column_name].agg(['mean', 'std']).reset_index(drop=False)
    group_data['low_limit'] = group_data['mean'] - 3 * group_data['std'] # расчитываем лимит
    main = data.merge(group_data, how='left', on=['DC', 'h', 'm'])
    main['incident_A'] = (main[column_name] < main['low_limit']).astype(int) # 1 - выход за пределы распределения (подозрение на инцидент)
    return main['incident_A'].values                                         # 0 - все хорошо

# определяем среднее значение выручки по дата центру, месяцу и часу
def get_mean(data):
    group_data = data.groupby(['DC', 'h', 'm'])['Spent'].agg(['mean']).reset_index(drop=False)
    main = data.merge(group_data, how='left', on=['DC', 'h', 'm'])
    return main['mean'].values

# Расчитываем показатели итоговой таблицы
def get_result_table(data):


    def duration_calculus(a):
        sm = 0
        itog = []
        for v in a:
            if v == 1:
                sm += 1
            else:
                if sm != 0:
                    itog.append(sm)
                    sm = 0
                else:
                    itog.append(1)
        if sm != 0:
            itog.append(sm)
        return np.asarray(itog).mean()


    main = data[(data['incident_A'] == 1) | (data['incident_B'] == 1)]
    main['Hour'] = pd.to_datetime(main['Hour'])
    main = main.sort_values("Hour")
    # количество и сумма потерь по инцидентам и дата центрам
    itog = main.groupby(['DC', 'incident_A', 'incident_B'])[['loss']].agg(['count', 'sum']).reset_index(drop=False)
    itog[('loss','sum')] = itog[('loss','sum')].astype(int)
    # среднее время между инцидентами и средняя продолжительность инцидентов по дата центрам
    other_main = main.groupby(['DC'])[['Hour']].agg([lambda x: (x.diff() / pd.Timedelta('1 hour'))[1:].values.mean(),
                                                    lambda x: duration_calculus((x.diff() / pd.Timedelta('1 hour'))[1:])
                                               ]).reset_index(drop=False
                                                              ).rename(columns={"<lambda_0>": 'mean_hours',
                                                                                "<lambda_1>": 'mean_duration'})
    return itog.merge(other_main,how='left',on=['DC'])


def main():
    main_fold="/Users/severex_u_r1/Ipython/Applovin_test/"
    data=pd.read_csv(os.path.join(main_fold,"report_task_1.csv"))
    data['h'] = pd.to_datetime(data['Hour']).dt.hour #выделяем часы с времени
    data['m'] = pd.to_datetime(data['Hour']).dt.month #выделяем месяцы с времени
    data['incident_A'] = get_incident(data, 'Bids')
    data['incident_B'] = get_incident(data, 'Impressions')
    data.loc[data['Spent'].isna(), 'incident_B'] = 1    # если нет данных по выручке, сервис аналитики скорее всего лежит
    data.loc[(data['Bids'].isna()) & (data['incident_B'] == 1), 'incident_A'] = 1 #  если нет данных по запросам
    # и по показам видим аномальное падение - значит сервис отправки запросов не работает
    data.loc[data['incident_A'] == 1, 'incident_B'] = 0 # для разграничения причинно следственной связи,
    # если случился инцидент А, то падение показов произошло из-за него, а не из-за падения сервиса аналитики
    data['mean_spent'] = get_mean(data)
    data[['Impressions', 'Spent']] = data[['Impressions', 'Spent']].fillna(0)
    data['A_loss'] = data['incident_A'] * np.where(data['mean_spent'] > data['Spent'],
                                                   data['mean_spent'] - data['Spent'], 0) # считаем потери как разницу
    # между текущей выручкой и средней по дата центру, месяцу и часу. В некоторых случаях при падении показов,
    # выручка остается на том же уровне, не знаю с чем это связано
    data['B_loss'] = data['incident_B'] * np.where(data['mean_spent'] > data['Spent'],
                                                   data['mean_spent'] - data['Spent'], 0)
    data['loss'] = data['A_loss'] + data['B_loss']
    result=get_result_table(data)
    result.loc[len(result)]=['total']+result.sum().to_list()[1:-2]+result.mean().to_list()[-2:]
    return result


print(main())
