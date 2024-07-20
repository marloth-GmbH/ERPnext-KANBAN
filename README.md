# ERPnext-KANBAN


Creates A7 Kanban cards from ERPnext items. 

## Reorder QR-Code 
the field: orderpage_link must be added to items. 
It is used to generate the reoder QR-Code on the back of the card. 
When it starts with 'http' a QR-Code will be generated. If not the text in that field will be printed. 

## Deploymend
We have a local NAS, that can run Containers. We use the docker-compose.yml to deploy it to this NAS. The APP the uses Flask to create a small website, that the employees can use. 
We have QR-Codes with the item_code on all Labels. So we can use our Scanner to collect a list of items. 


![grafik](https://github.com/user-attachments/assets/e1241a3a-1f1c-4fca-bcd1-c84a263d275b)


This script creates a PDF for KANBAN-Cards.

![grafik](https://github.com/user-attachments/assets/ab4f168d-dbf3-4be6-a1c4-888ce855f215)



The Cards are printed on A6 paper, that is then folded in half to create a double sided card and then laminated into an A7 pouche. 

![grafik](https://github.com/user-attachments/assets/c2f4d1fb-cc54-412f-8001-483401cee0e1)

