import requests

headers = {
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://goodwine.com.ua/ua/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "accept": "*/*",
    "authorization": "",
    "content-type": "application/json",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Linux",
    "store": "ua"
}

def load_img(url:str):
  response = requests.get(url, headers=headers)
  return response.content

def goodwine_search(name:str):
  name = name.replace('\n', '')
  url = "http://goodwine.com.ua/graphql"

  querystring = {"query":
                "query getAutocompleteResults($inputText: String!) {  products(search: $inputText, currentPage: 1, pageSize: 1, filter: {}) {    items {      name      small_image {        url      }      url_key      custom_attributes {        country        country_flag        region        producer      }      price {        regularPrice {          amount {            value            currency          }        }      }      special_price    }  }}"}
  querystring["variables"] = '{\"inputText\":\"NAME\"}'.replace('NAME', name)
  

  payload = ""


  response = requests.get(url, data=payload, headers=headers, params=querystring)
  if response.status_code == 200:
    return response.json()['data']['products']['items'][0]
  else:
    return None
  