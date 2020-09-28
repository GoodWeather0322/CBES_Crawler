# CBES Crawler

## Overview
[營業人統一編號資訊](https://www.etax.nat.gov.tw/cbes/web/CBES113W1_1) 爬蟲程式 
- 使用selenium模擬網頁
- 網頁驗證碼辨識

## 驗證碼辨識
- 使用 OpenCV 將驗證碼圖像進行二值化、銳利化
- 進行邊緣輪廓檢測，裁切出各個待辨識圖像，重新縮放大小
- 與[已標記正確答案](https://github.com/GoodWeather0322/CBES_Crawler/tree/master/captcha/True2)圖像計算MSE進行相似度判別，得到辨識結果
- 驗證碼辨識成功率為 92.3 %

<p align="center">

![original](/README/origin.png)

<img src="/README/origin.png">

&darr;

![binarization](/README/binarization.png)

&darr;

![f1](/README/fig0.png) ![f1](/README/fig1.png) ![f1](/README/fig2.png) ![f1](/README/fig3.png) ![f1](/README/fig4.png) ![f1](/README/fig5.png)

&darr;

![f1](/README/resize_fig0.png) ![f1](/README/resize_fig1.png) ![f1](/README/resize_fig2.png) ![f1](/README/resize_fig3.png) ![f1](/README/resize_fig4.png) ![f1](/README/resize_fig5.png)

&darr;

已標記資料庫

&darr;

# Result S 7 K G P R

</p>

## 輸入
|統一編號|類別|名稱|
| ---   | ---|---|
|99441140|商業登記|晶淳快餐店
|99441155|商業登記|大吉祥香豆富飲食店
|99441182|商業登記|荷蘭貓精品屋

## 輸出
|營業人統一編號|查看分支機構|負責人姓名|營業人名稱|營業（稅籍）登記地址|資本額(元)|組織種類|設立日期|登記營業項目|
|---|---|---|---|---|---|---|---|---|
|99441140|營業中|陳明傑|晶淳快餐店|新北市淡水區北新里北新路１８２巷２９號|200,000|獨資(6)|930303|便當、自助餐店( 561112 )|
|99441155|營業中|張右儒|大吉祥香豆富飲食店|新北市淡水區學府路１７１號（１樓）|120,000|獨資(6)|930303|麵店、小吃店( 561113 )|
|99441182|非營業中|羅怡蘋|荷蘭貓精品屋|桃園市中壢區普忠里實踐路７４號１樓|30,000|獨資(6)|930101|服裝零售( 473211 )|



