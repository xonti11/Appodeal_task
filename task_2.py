import pandas as pd
import os
pd.set_option("max_rows",100)

#  так как в каждую категорию в разрезе страна, приложение, цена, тип рекламы, DSP входит по 1, максимум 2 примера,
#  просто удаляем категории с наименьшей выручкой с запроса пока не потеряем 5 % выручки
def main():
    main_fold = "/Users/severex_u_r1/Ipython/Applovin_test/"
    data = pd.read_csv(os.path.join(main_fold, "report_task_2.csv"))
    data['revenue'] = data['bids'] * data['bidFloor']
    data['rev_per_request'] = data['revenue'] / data['requests']
    data.sort_values('rev_per_request', inplace=True)
    data['cum_revenue'] = data['revenue'].cumsum()
    restrict_income=data['revenue'].sum()*0.05
    data=data.rename(columns={'requests':'saved_requests'})
    data=data[data['cum_revenue'] < restrict_income].drop(['revenue','cum_revenue','rev_per_request','bids',
                                                           ],axis=1).reset_index(drop=True)
    print("Total Number of 'saved' requests {}".format(data['saved_requests'].sum()))
    return data

print(main())