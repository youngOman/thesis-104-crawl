import time
import random
import requests
import json
import pandas as pd


class Job104Spider():

    def search(self, keyword, max_mun=10, filter_params=None, sort_type='符合度', is_sort_asc=False):
        """搜尋職缺"""
        jobs = []
        total_count = 0

        url = 'https://www.104.com.tw/jobs/search/list'
        query = f'ro=0&kwop=7&keyword={keyword}&expansionType=area,spec,com,job,wf,wktm&mode=s&jobsource=2018indexpoc'
        if filter_params:
            # 加上篩選參數，要先轉換為 URL 參數字串格式
            query += ''.join([f'&{key}={value}' for key, value, in filter_params.items()])

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36',
            'Referer': 'https://www.104.com.tw/jobs/search/',
        }

        # 加上排序條件 (符合度排序)
        sort_dict = {
            '符合度': '1',
            '日期': '2',
            '經歷': '3',
            '學歷': '4',
            '應徵人數': '7',
            '待遇': '13',
        }
        sort_params = f"&order={sort_dict.get(sort_type, '1')}"
        sort_params += '&asc=1' if is_sort_asc else '&asc=0'
        query += sort_params

        page = 1
        while len(jobs) < max_mun:
            params = f'{query}&page={page}'
            r = requests.get(url, params=params, headers=headers)
            if r.status_code != requests.codes.ok:
                print('請求失敗', r.status_code)
                data = r.json()
                print(data['status'], data['statusMsg'], data['errorMsg'])
                break

            data = r.json()
            total_count = data['data']['totalCount']
            jobs.extend(data['data']['list'])

            if (page == data['data']['totalPage']) or (data['data']['totalPage'] == 0):
                break
            page += 1
            time.sleep(random.uniform(3, 5))

        return total_count, jobs[:max_mun]

    # 取得職缺詳細資料
    def get_job(self, job_id):
        url = f'https://www.104.com.tw/job/ajax/content/{job_id}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36',
            'Referer': f'https://www.104.com.tw/job/{job_id}'
        }

        r = requests.get(url, headers=headers)
        if r.status_code != requests.codes.ok:
            print('請求失敗', r.status_code)
            return

        data = r.json()
        return data['data']

    def search_job_transform(self, job_data):
        """將職缺資料轉換格式、補齊資料"""
        appear_date = job_data['appearDate']
        apply_num = int(job_data['applyCnt'])
        company_addr = f"{job_data['jobAddrNoDesc']} {job_data['jobAddress']}"

        job_url = f"https:{job_data['link']['job']}"
        job_company_url = f"https:{job_data['link']['cust']}"
        job_analyze_url = f"https:{job_data['link']['applyAnalyze']}"

        job_id = job_url.split('/job/')[-1]
        if '?' in job_id:
            job_id = job_id.split('?')[0]

        salary_high = int(job_data['salaryLow'])
        salary_low = int(job_data['salaryHigh'])

        job = {
            'job_id': job_id,
            'type': job_data['jobType'],
            'name': job_data['jobName'],  # 職缺名稱
            # 'desc': job_data['descSnippet'],  # 描述
            'appear_date': appear_date,  # 更新日期
            'apply_num': apply_num, # 應徵人數
            'apply_text': job_data['applyDesc'],  # 應徵人數描述
            'company_name': job_data['custName'],  # 公司名稱
            'company_addr': company_addr,  # 工作地址
            'job_url': job_url,  # 職缺網頁
            'job_analyze_url': job_analyze_url,  # 應徵分析網頁
            'job_company_url': job_company_url,  # 公司介紹網頁
            'lon': job_data['lon'],  # 經度
            'lat': job_data['lat'],  # 緯度
            'education': job_data['optionEdu'],  # 學歷
            'period': job_data['periodDesc'],  # 經驗年份
            'salary': job_data['salaryDesc'],  # 薪資描述
            'salary_high': salary_high,  # 薪資最高
            'salary_low': salary_low,  # 薪資最低
            'tags': job_data['tags'],  # 標籤
        }
        return job
    # 將薪資格式統一轉換為 月薪
    def convert_salary_to_mothly(self, salary_min, salary_max):
        ANNUAL_SALARY_THRESHOLD = 600000  # 年薪判斷閥值
        HOURLY_SALARY_THRESHOLD = 5000  # 設定時薪判斷閥值
        TYPICAL_MONTHLY_WORK_HOURS = 160  # 假設一個月工時

        if salary_max > ANNUAL_SALARY_THRESHOLD:  # 如果是年薪
            return salary_min / 12, salary_max / 12
        elif salary_max < HOURLY_SALARY_THRESHOLD:  # 如果是時薪
            return salary_min * TYPICAL_MONTHLY_WORK_HOURS, salary_max * TYPICAL_MONTHLY_WORK_HOURS
        else:  # 如果是月薪直接返回
            return salary_min, salary_max


if __name__ == "__main__":
    job104_spider = Job104Spider()

    filter_params = {
        'sr': 99,  # (有寫薪資)
        # 'area': '6001001000,6001016000',  # (地區) 台北市,高雄市
        # 'isnew': '0',  # (更新日期) 0:本日最新 3:三日內 7:一週內 14:兩週內 30:一個月內
        # 's9': '1,2,4,8',  # (上班時段) 日班,夜班,大夜班,假日班
        # 's5': '0',  # 0:不需輪班 256:輪班
        # 'wktm': '1',  # (休假制度) 週休二日
        # 'jobexp': '1,3,5,10,99',  # (經歷要求) 1年以下,1-3年,3-5年,5-10年,10年以上
        # 'newZone': '1,2,3,4,5',  # (科技園區) 竹科,中科,南科,內湖,南港
        # 'zone': '16',  # (公司類型) 16:上市上櫃 5:外商一般 4:外商資訊
        # 'wf': '1,2,3,4,5,6,7,8,9,10',  # (福利制度) 年終獎金,三節獎金,員工旅遊,分紅配股,設施福利,休假福利,津貼/補助,彈性上下班,健康檢查,團體保險
        # 'edu': '1,2,3,4,5,6',  # (學歷要求) 高中職以下,高中職,專科,大學,碩士,博士
        # 'remoteWork': '1',  # (上班型態) 1:完全遠端 2:部分遠端
        # 'excludeJobKeyword': '科技',  # 排除關鍵字
        # 'kwop': '1',  # 只搜尋職務名稱
    }
    total_count, jobs = job104_spider.search('軟體工程師', max_mun=9999, filter_params=filter_params)

    print('搜尋結果職缺總數：', total_count)
    print("指定抓取職缺數", len(jobs))
    # jobs = [job104_spider.search_job_transform(job) for job in jobs]
    # print(jobs[0])
    all_job_details = []
    for job in jobs:
        job_link = job['link']['job']
        # job_id = job_link.split('/job/') # 返回結果: ['://www.104.com.tw', '86upm?jobsource=hotjob_chr']
        job_id = job_link.split('/job/')[-1].split('?')[0]  # 返回結果: 86upm
        print(job_id)

        job_details = job104_spider.get_job(job_id)

        if job_details is None:
            print(f"Failed to retrieve details for job ID: {job_id}")
            continue  # 跳過 None 值職缺.

        # 擷取並分割擅長工具多個物件，用逗號分隔 Ex: Python, Java, C, C++, C#
        # 可能會有 job_details['condition'] 這個物件本身是 None，所以要多 job_details['condition'].get('specialty') is not None
        if 'condition' in job_details and job_details['condition'] is not None and job_details['condition'].get('specialty') is not None:
            tools_description = ', '.join([tool['description'] for tool in job_details['condition']['specialty']])
        else:
            tools_description = '不拘'

        # 將薪資格式統一轉換為 月薪
        salary_min, salary_max = job104_spider.convert_salary_to_mothly(job_details['jobDetail']['salaryMin'], job_details['jobDetail']['salaryMax'])

        # 過濾最高薪資 & 最低薪資 為 9999999, 0 的職缺
        if job_details['jobDetail']['salaryMax'] != 0 and job_details['jobDetail']['salaryMax'] != 9999999 and job_details['jobDetail']['salaryMin'] != 0:
            all_job_details.append({
                # '職缺名稱': job_details['header']['jobName'],
                # '公司名稱': job_details['header']['custName'],
                '員工人數': job_details['employees'],
                
                '最高薪資': salary_max,
                '最低薪資': salary_min,
                # '薪資範圍': job_details['jobDetail']['salary'],
                '工作地區': job_details['jobDetail']['addressArea'],

                '是否需出差外派': job_details['jobDetail']['businessTrip'],
                '職務內容': job_details['jobDetail']['jobDescription'],
                # '休假制度': job_details['jobDetail']['vacationPolicy'],
                # '上班時段': job_details['jobDetail']['workPeriod'],

                '工作經歷要求': job_details.get('condition', {}).get('workExp', '不拘'),
                '學歷要求': job_details.get('condition', {}).get('edu', '不拘'),
                '科系要求': job_details.get('condition', {}).get('major', '不拘'),
                '其他條件': job_details.get('condition', {}).get('other', '不拘'),

                '擅長工具': tools_description,
                '相關產業': job_details['industry'],
                # '職缺連結': f"https://www.104.com.tw/job/ajax/content/{job_id}",
            })
            print(f"擷取中...{job_details['header']['jobName']}")
    print(all_job_details)

    # 單筆職缺資料 測試
    # job_info = job104_spider.get_job('6lo87')  # 取得職缺詳細資料
    # # print(job_info)
    # interested_data = [{
    #     '職缺名稱': job_info['header']['jobName'],
    #     '公司名稱': job_info['header']['custName'],
    #     '最高薪資': job_info['jobDetail']['salaryMax'],
    #     '最低薪資': job_info['jobDetail']['salaryMax'],
    # }]
    # print(interested_data)

    # 將列表輸出為 JSON 檔案
    # with open("104_data.json", "w", encoding="utf-8") as file:
    #     json.dump(job_info, file, indent=2, sort_keys=True, ensure_ascii=False)
    # print("爬蟲結束，存檔完成，檔名:104_data.json")

    # 將列表轉換為 DataFrame，並輸出為 Excel 檔案
    # df = pd.DataFrame([all_job_details]) # 單筆才需加 []

    df = pd.DataFrame(all_job_details)
    
    file_name = '104_data_20240503.xlsx'
    df.to_excel(file_name, index=False)
    print(f"爬蟲結束，資料已匯出為 Excel 檔案:{file_name}")
