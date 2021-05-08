import requests
import sys
import pprint
import os
from datetime import date
import json
from requests.api import delete
from simple_term_menu import TerminalMenu, main

# Get auth token

base_url = 'http://127.0.0.1:8000/'
data_auth = {
    "username": '',
    "password" : ''
}

auth_url = base_url + 'token'
auth_headers = {'content-type': 'application/x-www-form-urlencoded'}
res = requests.post(url = auth_url, headers=auth_headers, data=data_auth)
access_token = res.json()['access_token']
get_headers ={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)}



def calc_day_summary(todays_data):

    stats = {
        'calories': 0,
        'protein' : 0,
        'carbs' : 0,
        'fats' : 0
        }

    for item in todays_data:
        for key in stats.keys():
            stats[key] += item[key] * item['quantity']

    return stats 

def show_daily_eating(todays_data):
    print("\nToday's eating")
    [print(f"* {item['name']} x {item['quantity']} = {int(item['calories'] * item['quantity'])}cals") for item in todays_data]
    daily_stats = calc_day_summary(todays_data)
    print("")
    print("cals: " + str(int(daily_stats['calories'])))
    print("p: " + str(int(daily_stats['protein'])))
    print("c: " + str(int(daily_stats['carbs'])))
    print("f: " + str(int(daily_stats['fats'])))
    print("")
    return

def delete_item():

    todays_data = get_todays_data()
    tracking_url = base_url + 'api/tracking'

    delete_list = [f"{item['name']} x {item['quantity']} ({item['id']})" for item in todays_data]
    #print(delete_list)
    delete_menu = TerminalMenu(delete_list, title = "----- Delete tracked item -----")
    menu_entry_index = delete_menu.show()
    tracking_id_to_delete =  todays_data[menu_entry_index]['id'] 
    
    #data_del = {"id_to_del": tracking_id_to_delete}
    res_d = requests.delete(tracking_url+ '?id_to_del=' + str(tracking_id_to_delete), headers=get_headers)
    #print(res_d.json())
    return 


def add_item():

    tracking_url = base_url + 'api/tracking'
    masterlist_url = base_url + 'api/foods'
    res_m = requests.get(masterlist_url, headers=get_headers)
    masterlist_data = res_m.json()

    # Adding a new item
    list_of_names = [f"{item['name']} cals:{item['calories']}" for item in masterlist_data]
    list_of_names.append("None")
    terminal_menu = TerminalMenu(list_of_names, title = "----- Add a tracked item -----")
    menu_entry_index = terminal_menu.show()

    if menu_entry_index != len(list_of_names)-1:
        print(masterlist_data[menu_entry_index]['name'])
        food_quantity = input("Quantity: ")

        data_food_item = {
        "food_id": int(masterlist_data[menu_entry_index]['id']),
        "quantity": float(food_quantity),
        "date": str(date.today())
        }

        res_p = requests.post(tracking_url, data=json.dumps(data_food_item), headers=get_headers)
        #print(res_p.json())
    
    return


def get_todays_data():
    today = str(date.today())
    get_headers ={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)}

    tracking_get_url = base_url + 'api/trackingmerged'
    res_t = requests.get(tracking_get_url, headers=get_headers)
    tracking_data = res_t.json()

    todays_data = [item for item in tracking_data if item["date"] == today]
    return todays_data



def main():
   
    main_menu = TerminalMenu(['Add Item', 'Remove Item', "Exit"], title = "-------------------")
    main_menu_index = None

    while main_menu_index != 2:
        os.system('clear')
        show_daily_eating(get_todays_data())
        main_menu_index = main_menu.show()
        
        if main_menu_index == 0:
            add_item()
            
        elif main_menu_index == 1:
            delete_item()
            
    exit()


if __name__== '__main__':
    main()


#import pdb; pdb.set_trace()

