import feedparser
from bs4 import BeautifulSoup, element
from urllib import request
from urllib.request import urlretrieve
import lxml
import html5lib
import bleach
from tqdm import tnrange, tqdm
import json
import time
from pathlib import Path
import requests
from xml.etree import ElementTree as ET
import re
import os

from tqdm import tqdm_notebook

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from multiprocessing import Pool

import pandas as pd
import tempfile

import numpy as np
import cv2
import matplotlib.pyplot as plt

name2img = {}

vat_list_file = "vat_number_list.csv"
output_file = 'output.xls'
no_data_file = 'no_data.xls'
temp_path = 'tmp'

main_url = 'https://www.etax.nat.gov.tw/'
url = main_url + 'cbes/web/CBES113W1_1'

total_data_count, total_search_count = 0, 0

for file in Path("captcha/True2/").glob('*.png'):
    name = file.stem
    image = cv2.imread(str(file))
    
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    ret,image = cv2.threshold(image,150,255,cv2.THRESH_BINARY)

    
    name2img[name] = image.copy()

def mse(image1, image2):
    err = np.sum((image1.astype('float') - image2.astype('float')) ** 2)
    err /= float(image1.shape[0] * image2.shape[1])
    
    return err

def captcha_solver(image):
#     image = cv2.imread(str(file))
    cut = 1
    image = image[cut:-cut, cut:-cut, :]
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    ret,image = cv2.threshold(image,150,255,cv2.THRESH_BINARY)

    image[image==255] = 10
    image[image==0]=255
    image[image==10]=0

    # kernal = np.ones((3, 3), np.uint8)
    # image = cv2.erode(image, kernal, iterations=1)

    # image = cv2.GaussianBlur(image, (3, 3), 0)

    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32) #锐化
    image = cv2.filter2D(image, -1, kernel=kernel)

    # image = cv2.Canny(image, 30, 150)
    # image = np.clip(image, 0, 255)
    # image = np.array(image,np.uint8)
    
    image_, contours, hierarchy = cv2.findContours(image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)
    cnts = sorted([(c, cv2.boundingRect(c)[0]) for c in contours], key=lambda x:x[1])
    
    ary = []
    for (c, _) in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
    #     print(x, y, w, h)
        if w > 12 and h > 15:
            ary.append((x, y, w, h))
            
    bests = []
    
    for i ,(x, y, w, h) in enumerate(ary):
        roi = image[y:y+h, x:x+w]
        thresh = roi.copy()

        total_size = 50
        top = int((total_size - thresh.shape[0]) / 2)
        bottom = total_size - top - thresh.shape[0]
        left = int((total_size - thresh.shape[1]) / 2)
        right = total_size - left - thresh.shape[1]

        res= cv2.copyMakeBorder(thresh,top,bottom,left,right,cv2.BORDER_CONSTANT,value=[0, 0, 0])

        score_dict = {}
        for name, img in name2img.items():
            err = mse(res, img)
            score_dict[name] = err

        best = ['none', np.inf]
        for name, score in score_dict.items():
            if score < best[1]:
                best = [name, score]

        bests.append(best)
        
    while len(bests) > 6:
        highest = 0
        highest_idx = -1
        for i, best in enumerate(bests):
            if best[1] > highest:
                highest_idx = i
                highest = best[1]
        bests.remove(bests[highest_idx])

    words = [w.split('-')[0] for [w,s] in bests]
    return ''.join(words)

def crawler(vat_list):
    
    data_count = len(vat_list)
    search_count = 0
    
    dl_pic = tempfile.NamedTemporaryFile(suffix='.png', dir=temp_path).name
    screen_shot = tempfile.NamedTemporaryFile(suffix='.png', dir=temp_path).name

    vat_number = '04126516'
    captcha_code = 'ABCDEz'

    try_step = 10

    driver = webdriver.Chrome()
    
    crawler_dict = {}

    for vat_number in vat_list:
        
        vat_number = str(vat_number)

#         print('='*30)
        print('now find {}'.format(vat_number))

        for step in range(try_step):
            
            search_count += 1

            # driver = webdriver.Chrome()

            driver.get(url)
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "container-fluid"))
                )
            finally:
            #     print(driver.page_source)
                soup = BeautifulSoup(driver.page_source,"lxml")


            vat = driver.find_element_by_id('vatId')
            vat.clear()
            vat.send_keys(vat_number)

            driver.save_screenshot(screen_shot)
            captcha_img = driver.find_element_by_id('captchaImg')
            size = captcha_img.size
            loc = captcha_img.location
            image = cv2.imread(str(screen_shot))
            image = image[loc['y']:loc['y']+size['height'], loc['x']:loc['x']+size['width']]

            captcha_code = captcha_solver(image)
    #         captcha_code='AAAAAA'

            captcha = driver.find_element_by_id('captcha')
            captcha.clear()
            captcha.send_keys(captcha_code)

            submut_btn = driver.find_element_by_xpath('//*[@id="tablet01"]/table/tbody/tr[3]/td/div/div[1]/input')
            submut_btn.click()

            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="tablet01"]'))
                )
            finally:
                soup = BeautifulSoup(driver.page_source,"lxml")

    #         print(driver.find_element_by_xpath('//*[@id="tablet01"]').text)
            if '請輸入正確的資料' in driver.find_element_by_xpath('//*[@id="tablet01"]').text:
                print('vat_number {} error'.format(vat_number))
                break
            elif '驗證碼錯誤' in driver.find_element_by_xpath('//*[@id="tablet01"]').text:
                if step == try_step-1:
                    print('get vat number {} failed over {} times'.format(vat_number, try_step))
                else:
                    print('captcha code recog error, try again .. {}'.format(step+1))
            elif '營業人統一編號' in driver.find_element_by_xpath('//*[@id="tablet01"]').text:
#                 print('success in')
                
                info_dict = {}

                businessIdHeader = driver.find_element_by_id("businessIdHeader").text
                businessId = driver.find_element_by_id("businessId").text

                operatingStatusHeader = driver.find_element_by_id("operatingStatusHeader").text
                if operatingStatusHeader[-1] == '：':
                    operatingStatusHeader = operatingStatusHeader[:-1]
                status = driver.find_element_by_id("status").text

                ownerNameHeader = driver.find_element_by_id("ownerNameHeader").text
                ownerName = driver.find_element_by_id("ownerName").text

                businessNameHeader = driver.find_element_by_id("businessNameHeader").text
                businessName = driver.find_element_by_id("businessName").text

                addressHeader = driver.find_element_by_id("addressHeader").text
                address = driver.find_element_by_id("address").text

                capitalHeader = driver.find_element_by_id("capitalHeader").text
                capital = driver.find_element_by_id("capital").text

                organizationTypeHeader = driver.find_element_by_id("organizationTypeHeader").text
                organizationType = driver.find_element_by_id("organizationType").text

                registerDateHeader = driver.find_element_by_id("registerDateHeader").text
                registerDate = driver.find_element_by_id("registerDate").text

                registerTypeHeader = driver.find_element_by_id("registerTypeHeader").text
                registerType = driver.find_element_by_id("registerType").text.split('\n\n')[0]
                if '有關營業登記資料記載內容' in registerType :
                    registerType = ''
                
                info_dict[businessIdHeader] = businessId
                info_dict[operatingStatusHeader] = status
                info_dict[ownerNameHeader] = ownerName
                info_dict[businessNameHeader] = businessName
                info_dict[addressHeader] = address
                info_dict[capitalHeader] = capital
                info_dict[organizationTypeHeader] = organizationType
                info_dict[registerDateHeader] = registerDate
                info_dict[registerTypeHeader] = registerType
                
                
                crawler_dict[vat_number] = info_dict
                
                break
            
    driver.close() 
    return crawler_dict, data_count, search_count

if __name__ == '__main__':

    vat_csv = pd.read_csv(vat_list_file)
    total_vat_list = vat_csv['統一編號'].tolist()
    total_vat_list = total_vat_list[20050:20150]
    total_vat_dict = {str(vat_number):0 for vat_number in total_vat_list}

    if Path(output_file).exists():
        print('exists {}, try to load it...'.format(output_file))
        vat_saved = pd.read_excel(output_file)
    else:
        vat_saved = pd.DataFrame(columns = ["營業人統一編號", "查看分支機構", '負責人姓名', '營業人名稱', '營業（稅籍）登記地址', '資本額(元)', '組織種類', '設立日期', '登記營業項目'])
        vat_saved.to_excel(output_file, index=False)
        
    if Path(no_data_file).exists():
        print('exists {}, try to load it...'.format(no_data_file))
        no_data_vat = pd.read_excel(no_data_file)
    else:
        no_data_vat = pd.DataFrame(columns = ["營業人統一編號查無資料"])
        no_data_vat.to_excel(no_data_file, index=False)
        
    already_save = vat_saved['營業人統一編號'].tolist()
    already_save_dict = {str(vat_number):0 for vat_number in already_save}
    no_data_vat_list = no_data_vat["營業人統一編號查無資料"].tolist()
    no_data_vat_dict = {str(vat_number):0 for vat_number in no_data_vat_list}
    print('total {} data'.format(len(total_vat_dict)))
    print('previous already done {} data'.format(len(already_save_dict) + len(no_data_vat_dict)))
    for vat_number in already_save_dict:
        if vat_number in total_vat_dict:
            del total_vat_dict[vat_number]
            
    for vat_number in no_data_vat_dict:
        if vat_number in total_vat_dict:
            del total_vat_dict[vat_number]
            
            
    print('remain {} data, start to crawl them...'.format(len(total_vat_dict)))
    total_vat_list = list(total_vat_dict.keys())

    save_point = 500
    save_count = int(len(total_vat_list) / save_point) + 1 if len(total_vat_list) % save_point!= 0 else int(len(total_vat_list) / save_point)

    vat_lists = []
    for i in range(save_count):
        vat_list = total_vat_list[save_point*i:save_point*i+save_point]
    #     print('vat_list_len', len(vat_list))
        vat_lists.append(vat_list)

    for vat_list in vat_lists:
        one_group = 10
        group_count = int(len(vat_list) / one_group) + 1 if len(vat_list) % one_group!= 0 else int(len(vat_list) / one_group)
    #     print('group_count', group_count)
        sub_lists = []
        for i in range(group_count):
            sub_list = vat_list[one_group*i:one_group*i+one_group]
    #         print('sub_list', len(sub_list))
            sub_lists.append(sub_list)
            
        pool = Pool(processes=24)
        return_list = []
        
        for sub_list in sub_lists:
            return_list.append(pool.apply_async(crawler, args=(sub_list, )))
            
        pool.close()
        pool.join()
        
        save_dict = {}
        no_data_dict = {}
        for value in return_list:
            try:
                crawler_dict, data_count, search_count = value.get()
                total_data_count += data_count
                total_search_count += search_count
            except:
                continue

            for vat_number, info_dict in crawler_dict.items():
                if info_dict['營業人統一編號'] != '您輸入的統一編號 查無資料':
                    save_dict[vat_number] = info_dict
                else:
                    no_data_dict[vat_number] = {"營業人統一編號查無資料":vat_number}
                
        print('success crawl {} data, save it'.format(len(save_dict) + len(no_data_dict)))
        print('error rate : {}'.format( (total_search_count-total_data_count) / total_data_count) )
        
        
        for k, v in save_dict.items():
            vat_saved = vat_saved.append(v, ignore_index=True)
            
        for k, v in no_data_dict.items():
            no_data_vat = no_data_vat.append(v, ignore_index=True)
            
        vat_saved.to_excel(output_file, index=False)
        no_data_vat.to_excel(no_data_file, index=False)

    print('clean temp file...')
    for _file in Path(temp_path).glob('*'):
        os.remove(str(_file))
    
