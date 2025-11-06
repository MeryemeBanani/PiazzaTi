import requests
fullPdf = r"C:\Users\Merye\Desktop\LA_PIAZZA\PiazzaTi\NLP\cv_json_to_dataset\cv_example\cv_0342_Ilaria_Barbieri_IT.pdf"
url = "http://127.0.0.1:8000/parse/upload?background=false"
with open(fullPdf, "rb") as f:
    files = {"file": ("cv.pdf", f, "application/pdf")}
    data = {"user_id": "USER_006", "Tags": '{"women_in_tech":true,"1_2_generation":true}'}
    r = requests.post(url, files=files, data=data)
    print("Status:", r.status_code)
    print(r.text)