from config import companies, max_page
from collector import format_negative_news_many, pd


excel = pd.ExcelWriter('企业预警.xlsx')
for name, cid in companies.items():
    data = format_negative_news_many(cid, max_page)
    data.to_excel(excel, sheet_name=name)
excel.save()
excel.close()
