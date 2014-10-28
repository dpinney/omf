import xlwt
import json

wb = xlwt.Workbook()
sh1 = wb.add_sheet("All Input Data")
inJson = json.load(open("allInputData.json"))
size = len(inJson.keys())
for i in range(size):
    sh1.write(i, 0, inJson.keys()[i])

for i in range(size):
    sh1.write(i, 1, inJson.values()[i])

outJson = json.load(open("allOutputData.json"))
sh1.write(0, 5, "Lat")
sh1.write(0, 6, "Lon")
sh1.write(0, 7, "Elev")
sh1.write(1, 5, outJson["lat"])
sh1.write(1, 6, outJson["lon"])
sh1.write(1, 7, outJson["elev"])

sh2 = wb.add_sheet("Houly Data")
sh2.write(0, 0, "TimeStamp")
sh2.write(0, 1, "Power(W-AC)")
sh2.write(0, 2, "Difuse Irradiance (W/m^2)")
sh2.write(0, 3, "Direct Irradiance (W/m^2)")
sh2.write(0, 4, "Wind Speed (m/s)")
sh2.write(0, 5, "Ambient Temperature (F)")
sh2.write(0, 6, "Cell Temperature (F)")

for i in range(8760):
    sh2.write(i + 1, 0, outJson["timeStamps"][i])
    sh2.write(i + 1, 1, outJson["powerOutputAc"][i])
    sh2.write(i + 1, 2, outJson["climate"]["Difuse Irradiance (W/m^2)"][i])
    sh2.write(i + 1, 3, outJson["climate"]["Direct Irradiance (W/m^2)"][i])
    sh2.write(i + 1, 4, outJson["climate"]["Wind Speed (m/s)"][i])
    sh2.write(i + 1, 5, outJson["climate"]["Ambient Temperature (F)"][i])
    sh2.write(i + 1, 6, outJson["climate"]["Cell Temperature (F)"][i])

sh2.panes_frozen = True
sh2.vert_split_pos = 1

sh3 = wb.add_sheet("Monthly Data")
sh3.write(0, 1, "Monthly Generation")
for i in range(24):
    sh3.write(0, 3 + i, i + 1)
for i in range(12):
    sh3.write(i + 1, 0, outJson["monthlyGeneration"][i][0])
    sh3.write(i + 1, 1, outJson["monthlyGeneration"][i][1])
for i in range(len(outJson["seasonalPerformance"])):
    sh3.write(outJson["seasonalPerformance"][i][1] + 1, outJson["seasonalPerformance"]
              [i][0] + 3, outJson["seasonalPerformance"][i][2])
sh3.panes_frozen = True
sh3.vert_split_pos = 3
sh3.horz_split_pos = 1

sh4 = wb.add_sheet("Annual Data")
sh4.write(0, 0, "Year No.")
for i in range(30):
    sh4.write(i + 1, 0, i)
sh4.write(0, 1, "Net Cash Flow ($)")
sh4.write(0, 2, "Life O&M Costs ($)")
sh4.write(0, 3, "Life Purchase Costs ($)")
sh4.write(0, 4, "Cumulative Cash Flow ($)")
for i in range(30):
    sh4.write(i + 1, 1, outJson["netCashFlow"][i])
    sh4.write(i + 1, 2, outJson["lifeOmCosts"][i])
    sh4.write(i + 1, 3, outJson["lifePurchaseCosts"][i])
    sh4.write(i + 1, 4, outJson["cumCashFlow"][i])

sh4.write(0, 10, "ROI")
sh4.write(1, 10, outJson["ROI"])
sh4.write(0, 11, "NPV")
sh4.write(1, 11, outJson["NPV"])
sh4.write(0, 12, "IRR")
sh4.write(1, 12, outJson["IRR"])
# sh4.write(2, 11, xlwt.Formula("NPV(('All Input Data'!B15/100,'Annual Data'!B2:B31))"))
sh4.write(2, 12, xlwt.Formula("IRR(B2:B31)"))
wb.save("Sample Output.xls")
