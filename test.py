# with open('root/record_locations.txt','r') as file:
#     content=file.read()
import os
f=open('root/months/july.txt','r')
data=f.readlines()
def selection(s):
    for i in range(0,len(s)):
        s[i]=s[i].split('|')
    for i in range(0,len(s)-1):
        p=0
        mini=int(s[-1][1])
        for j in range(i,len(s)):
            if int(s[j][1])<=mini:
                mini=int(s[j][1])
                print(mini)
                p=j
        s[i],s[p]=s[p],s[i]
    for i in range(0,len(s)):
        s[i]='|'.join(s[i])
    print(s)
print(data)
selection(data)
# while(True):
#     data=f.readline()
#     data=data.split('|')
#     if data[0]!='44ad1854-a965-4f61-b152-238de74841b9':
#         break
#     print(data)
f.close()
# f=open('root/months/july.txt','rb')
# f.seek(470)
# data=f.read(470)
# f.close()
# print(data)
# f.close()