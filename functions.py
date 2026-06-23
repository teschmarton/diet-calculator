import datetime
from datetime import date
from requests import post
import api_key 
from json import loads

class Nutrients:
    attributes = (
    "carbohydrate", "protein", "fat", "fibre", "kCal")

    def __init__(self,carbohydrate:float=0.0, protein:float=0.0, fat:float=0.0, fibre:float=0.0, kCal:float=0.0):
        self.carbohydrate=carbohydrate
        self.protein=protein
        self.fat=fat
        self.fibre=fibre
        self.kCal=kCal

class Product:
    attributes = ("name", "nutri", "source", "amount")
    def __init__(self, name:str="", nutri:Nutrients=None, source:str="", amount:float=0.0):
        """

        :param name: name of the product
        :param nutri: nutri data
        :param source: source of nutri information
        :param amount: real weight to which the nutri data corresponds
        """
        self.name=name
        self.nutri=Nutrients() if nutri is None else nutri
        self.source=source
        self.amount=amount


class Pot:
    attributes = ("name", "weight")
    def __init__(self,name:str="",weight:float=0.0):
        """

        :param name: name of the pot
        :param weight: scale measured weight of pot
        """
        self.name=name
        self.weight=weight


class Target_nutri:
    attributes = ("name", "nutri")
    def __init__(self,name:str="", nutri:Nutrients=None):
        """
        :param name:
        :param nutri:
        """
        self.name=name
        self.nutri=Nutrients() if nutri is None else nutri

class Remaining_nutri:
    attributes = ("name", "nutri")
    def __init__(self,name:str="", nutri:Nutrients=None):
        """
        :param name:
        :param nutri:
        """
        self.name=name
        self.nutri=Nutrients() if nutri is None else nutri


class Weight_conversion:
    def __init__(self, number_of_data_pairs:int=8):
        """

        :param number_of_pairs: how many pairs does the txt have?
        """
        attributes=["name"]
        for i in range(1,number_of_data_pairs+1):
            exec(f"self.weight{i}=0")
            attributes.append(f"weight{i}")
        self.attributes=attributes
        self.name=""




back_to_main="-q"
yes_answer=("y", "yes", "ye", "yea", "yeah")


object_files={"product":"products.txt","product use":"use_product.txt","remaining nutri":"remaining_nutri.txt","weight conversion":"weight_conversion.txt","target nutri":"target_nutri.txt","pot":"pots.txt"}

object_classes={"product":Product,"remaining nutri":Remaining_nutri,"weight conversion":Weight_conversion, "target nutri":Target_nutri, "pot":Pot}


usda_db={"0":"Foundation","1":"SR Legacy","2":"Survey","3":"Branded","4":"Experimental"}

usda_kw={'"..."':'exact phrase e.g.: "green pepper"',r'...':'either words e.g.: green pepper','+':' makes a word required e.g.: +candy corn','-':'excludes foods having the word e.g.: candy -chocolate"','*':'matches any non-whitespace e.g.: *berry','()': 'denote grouping e.g.: pizza -(pepperoni sausage)',':':'specifies that the word must be present in a particular data element e.g.: description:cheese'}

usda_nutri_numbers={"203":"protein","204":"fat","205":"carbohydrate","291":"fibre","208":"kCal","958":"kCal"}

url1=rf"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key.key()}" 
url2=rf"https://api.nal.usda.gov/fdc/v1/foods?api_key={api_key.key()}" 

def list_usda_items(database:list,keyword:str,requireallwords:bool):
    """
    Performing USDA database search based on keyword
    """
    body = {
        "query": keyword,
        "dataType": database,
        "pageSize": 200,
        "pageNumber": 1,
        "sortBy": "dataType.keyword",
        "sortOrder": "asc",
        "requireAllWords":requireallwords
    }
    r = post(url=url1, json=body)  
    response = loads(r.text)
    total_pages = int(response['totalPages'])
    all_foods=response["foods"]
    for i in range(2,total_pages+1):
        body["pageNumber"]=i
        r = post(url=url1, json=body)
        response = loads(r.text) 
        all_foods=all_foods+response["foods"]

    for i in all_foods:
        print(f"\tID: {i['fdcId']} ({i['foodCategory']} ; {i['dataType']} ; {i['publishedDate']}) - {i['description']}")

    return all_foods

def get_items_from_usda(fdcid:list)->list:
    body={
          "fdcIds": fdcid,
          "format": "abridged",
          "nutrients": [
            203, 
            204, 
            205, 
            291, 
            208, 
            
            958 

          ]}
    r=post(url=url2,json=body)
    response=loads(r.text)
    items=[]
    for i in response:
        prod=Product(i['description'],Nutrients(),"USDA",100)
        for j in i["foodNutrients"]:
            param=j["number"]
            setattr(prod.nutri,usda_nutri_numbers[param],float(j["amount"]))
        items.append(prod)

    return items


def load_objects(object_type:str,verbose:bool=True,data_separator:str="\t"):
    """Function that reads objects from file and returns them as a list.
    """
    object=object_classes[object_type]()
    object_file=object_files[object_type]
    expected_number_params=0
    separation_indices=[] 
    for i in object.attributes:
        try:
            separator=[expected_number_params,0]
            expected_number_params+=len(getattr(object,i).attributes)
            separator[1]=expected_number_params
            separation_indices.append(separator)
        except AttributeError:
            separator=[expected_number_params,0]
            expected_number_params+=1
            separator[1] = expected_number_params
            separation_indices.append(separator)

    reload=False
    while True:
        objects=[]
        try:
            with open(file=object_file,mode="r",encoding="utf-8") as f:
                raw=[i.strip().split(data_separator) for i in f.readlines()]
            if object_type!="remaining nutri" and len(raw) == 0:
                print(f"{object_file} is completely empty!")
                objects=add_object(objects,object_type)
                reload=True
            else:
                for i in raw:
                    try:
                        outer_object=object_classes[object_type]()

                        for j,k in zip(outer_object.attributes, separation_indices):
                            inner_object = getattr(outer_object, j)
                            for l, h in zip(range(k[0],k[1]),range(0,k[1]-k[0])):
                                if type(inner_object) in list(object_classes.values())+[Nutrients]:
                                    if type(getattr(inner_object,inner_object.attributes[h])) in (float,int):
                                        setattr(inner_object,inner_object.attributes[h], float(i[l]))
                                    elif type(getattr(inner_object,inner_object.attributes[h])) is str:
                                        setattr(inner_object, inner_object.attributes[h], i[l])

                                    
                                else:
                                    if type(inner_object) in (float, int):
                                        setattr(outer_object, j, float(i[l]))
                                    elif type(inner_object) is str:
                                        setattr(outer_object, j, i[l])

                        objects.append(outer_object)

                    except IndexError:
                        print(
                            f"Row {i} in {object_file} is either empty or has less than {expected_number_params} parameters! Check the Tabs also! Correct data:")
                        objects = add_object(objects, object_type)
                        reload=True

                    except ValueError:
                        print(f"Some data in {object_file}'s {i} row, that should be a number, is not! Correct data:")
                        objects = add_object(objects, object_type)
                        reload=True
            break

        except FileNotFoundError:
            print(f"{object_file} did not exist! File got created.")
            with open(object_file,mode="w") as f:
                pass

    if verbose==True:
        print(f"Loading {object_type} data from {object_file} was successful.")

    if reload==True:
        write_objects_to_file(objects,object_type)
    
    
    
    return objects


def add_object(objects:[object,...],object_type:str) -> [object,
                                              ...]:  
    """
    Function that adds new object(s) to the list containing objects.
    :param objects: [object1,object2,...,]
    :param object_type: {"product":Product or "pot":Pot or "target nutri":Target_nutri}
    :return: [object1,object2,...,] but without one given object
    """
    object_names = [i.name for i in objects]

    while True:
        help = 1
        while True:
            object_name = input("Name: ").strip()
            if object_name.lower()=="help" and help==1:
                help-=1
                for i in object_names:
                    print(i)
            elif object_name.lower() == back_to_main:
                return main()
            elif object_name not in object_names and object_name != "":
                break
            else:
                print(f"{object_name} is already in the {object_type} database, or given name is invalid!")

        outer_object = object_classes[object_type]()
        setattr(outer_object,outer_object.name,object_name)

        for i in outer_object.attributes[1:]:
            while True:
                if type(getattr(outer_object,i)) in (float, int):
                    try:
                        inp = input(f"{object_name}'s {i} parameter: ").strip()
                        if inp.lower() == back_to_main:
                            return main()
                        setattr(outer_object, i, float(inp))
                        break
                    except ValueError:
                        print(f"Parameter {i} has to be a number!")

                elif type(getattr(outer_object,i)) is str:
                    inp = input(f"{object_name}'s {i} parameter: ").strip()
                    if inp.lower() == back_to_main:
                        return main()
                    elif inp == "":
                        print("Empty input!")
                    else:
                        setattr(outer_object, i, inp)
                        break

                else:
                    inner_object=getattr(outer_object,i)
                    for j in inner_object.attributes:
                        while True:
                            inp = input(f"{object_name}'s {j} parameter: ").strip()
                            if inp.lower() == back_to_main:
                                return main()
                            if type(getattr(inner_object, j)) in (float,int):
                                try:
                                    setattr(inner_object, j, float(inp))
                                    break
                                except ValueError:
                                    print(f"Parameter {j} has to be a number!")
                            elif type(getattr(inner_object, j)) is str:
                                if inp=="":
                                    print("Empty input!")
                                else:
                                    setattr(inner_object, j, float(inp))
                                    break

                    
                    break

        objects.append(outer_object)
        object_names.append(object_name)

        if input(f"Do you want to add any other {object_type}? ").strip() not in yes_answer:
            break

    return objects


def modify_object(objects:[object,...],object_type:str) -> [object,
                                              ...]:  
    """
    Function that modifies object(s) in the list containing objects.
    :param objects: [object1,object2,...,]
    :param object_type: {"product":Product or "pot":Pot or "target nutri":Target_nutri}
    :return: [object1,object2,...,] but without one given object
    """

    object_names = [i.name for i in objects]

    while True:
        help = 1
        while True:
            object_name = input("Name: ").strip()
            if object_name.lower()=="help" and help==1:
                help-=1
                for i in object_names:
                    print(i)
            elif object_name.lower() == back_to_main:
                return main()
            elif object_name not in object_names:
                print(f"{object_name} is not in the {object_type} database!")
            else:
                break

        index=object_names.index(object_name)
        outer_object = objects[index]
        objects.pop(index)
        object_names.pop(index)

        for i in outer_object.attributes:
            while True:

                if type(getattr(outer_object, i)) in (float, int):
                    try:
                        inp = input(
                            f"{object_name}'s {i} parameter (current value is {getattr(outer_object, i)}): ").strip()

                        if inp.lower() == back_to_main:
                            return main()
                        elif inp.lower()=="-":
                            break
                        else:
                            setattr(outer_object, i, float(inp))
                            break
                    except ValueError:
                        print(f"Parameter {i} has to be a number!")

                elif type(getattr(outer_object, i)) is str:
                    inp = input(
                        f"{object_name}'s {i} parameter (current value is {getattr(outer_object, i)}): ").strip()

                    if inp.lower() == back_to_main:
                        return main()
                    elif inp.lower() == "-":
                        break
                    elif inp == "":
                        print("Empty input!")
                    else:
                        setattr(outer_object, i, inp)
                        break

                else:  
                    inner_object = getattr(outer_object, i)
                    for j in inner_object.attributes:
                        while True:
                            inp = input(f"{object_name}'s {j} parameter (current value is {getattr(inner_object,j)}): ").strip()
                            if inp.lower() == back_to_main:
                                return main()
                            elif inp.lower() == "-":
                                break
                            if type(getattr(inner_object, j)) in (float, int):
                                try:
                                    setattr(inner_object, j, float(inp))
                                    break
                                except ValueError:  
                                    print(f"Parameter {j} has to be a number!")
                            elif type(getattr(inner_object, j)) is str:
                                if inp == "":
                                    print("Empty input!")
                                else:
                                    setattr(inner_object, j, float(inp))
                                    break

                    
                    break

        objects.append(outer_object)
        object_names.append(outer_object.name)

        if input(f"Do you want to modify any other {object_type}? ").strip() not in yes_answer:
            break

    return objects

def delete_object(objects:[object,...],object_type:str)->[object,...]:
    """
    Function that deletes object(s) from the list containing objects.
    :param objects: [object1,object2,...,]
    :param object_type: {"product":Product or "pot":Pot or "target nutri":Target_nutri}
    :return: [object1,object2,...,] but without one given object
    """

    object_names = [i.name for i in objects]

    while True:
        help = 1
        while True:
            object_name = input("Name: ").strip()
            if object_name.lower()=="help" and help==1:
                help-=1
                for i in object_names:
                    print(i)
            elif object_name.lower() == back_to_main:
                return main()
            elif object_name not in object_names:
                print(f"{object_name} is not in the {object_type} database!")
            else:
                break

        index = object_names.index(object_name)
        objects.pop(index)
        object_names.pop(index)

        if input(f"Do you want to delete any other {object_type}? ").strip() not in yes_answer:
            break

    return objects

def write_objects_to_file(objects:[object,...], object_type:str, mode:str="w",start_with_new_line:bool=False,separator:str="\t"):
    """
    Function that writes list containing objects to file.
    :param objects: list containing all the objects
    :param file: name of the file
    :param mode: whether writing or appending should occur
    :return: file with new/additional content
    """

    destiny_file=object_files[object_type]

    if start_with_new_line == True:
        row = "\n"
    else:
        row = ""

    for i in range(0,len(objects)):
        object=objects[i]

        for j in object.attributes:
            if type(getattr(object,j)) not in list(object_classes.values())+[Nutrients]:
                row+=f"{getattr(object,j)}{separator}"
            else:
                for k in getattr(object,j).attributes:
                    row+=f"{getattr(getattr(object,j),k)}{separator}"
        row=row[:-1]
        row+="\n"
    row=row[:-1]

    with open(destiny_file,mode=mode,encoding="utf-8") as f:
        f.write(row)

    return print(f"Writing {object_type} data to {destiny_file} was successful.")
"""



objis=load_objects(txt6,9,{"scale":Scale},range(0,0))
for i in range(0,2):
    for j in range(1,9):
        print(getattr(objis[i],f"weight{j}"))
"""
def product_use_from_file(products:[Product,...])->[[Product,"amount"],[],...]:
    """
    Function that reads product-weight data pairs from file.
    :param products: list of products
    :return: list that has all the product-weight data pairs as content
    """
    product_names=[i.name for i in products]
    source=object_files["product use"]
    try:
        with open(source,mode="r",encoding="utf-8") as f:
            raw=f.readlines()
    except FileNotFoundError:
        print(f"{source} does not exist!")
        return product_use_manually(products, [])

    if len(raw) == 0:
        print(f"{source} is completely empty! Manual input... ")
        return product_use_manually(products, [])

    else:
        used_products=[]
        for i in raw:
            i = i.strip().split("\t")
            try:
                if i[0] not in product_names:
                    print(f"{i[0]} product is not in the product database! Correct data: ")
                    used_products=product_use_manually(products,used_products)
                else:
                    used_products.append([products[product_names.index(i[0])],float(i[1])])

            except ValueError:
                print(f"Weight data in product {i[0]} is not a number! Correct data: ")
                used_products=product_use_manually(products,used_products)
            except IndexError:
                print(f"There are less than 2 parameters in product {i[0]}! Check the Tabs also! Correct data: ")
                used_products=product_use_manually(products,used_products)

        return used_products

def product_use_manually(products:[Product,...], already_read_data:list)->[[Product,"amount"],[],...]:
    """
    Function that reads for manual product-weight data pairs.
    :param products: list of products
    :param already_read_data: list of already read product-weight data pairs
    :return:  list that has all the product-weight data pairs as content
    """

    product_names = [i.name for i in products]

    while True:
        help = 1
        while True:
            try:
                name=input("Name: ").strip()
                if name.lower()=="help" and help ==1:
                    help-=1
                    for i in product_names:
                        print(i)
                elif name.lower()==back_to_main:
                    return main()
                elif name not in product_names:
                    print(f"{name} is not in the product database!")
                else:
                    weight = float(input("Weight: ").strip())
                    break

            except ValueError:
                print("Parameter weight has to be a number!")
        
        already_read_data.append([products[product_names.index(name)],weight])
        
        if input("Are there any additional used products? ").strip() not in yes_answer:
            break
    
    return already_read_data    

def get_remaining_nutri()->Remaining_nutri:
    """
    Function that returns the remaining nutri object for today.
    :return: nutri data that has remained for the day
    """
    remaining_nutri=load_objects("remaining nutri")
    if len(remaining_nutri)==0 or remaining_nutri[-1].name.split(" ")[0]!=str(date.today()):
        target_nutris=load_objects("target nutri")
        if len(target_nutris) >1 :
            target_nutri_names=[i.name for i in target_nutris]
            help=1
            while True:
                name=input("Name of target nutri: ").strip()
                if name.lower()=="help" and help==1:
                    help-=1
                    for i in target_nutri_names:
                        print(i)
                elif name.lower()==back_to_main:
                    return main()
                elif name not in target_nutri_names:
                    print(f"{name} is not in the target nutri database!")
                else:
                    break
    
            remaining_nutri=target_nutris[target_nutri_names.index(name)]
        else:
            remaining_nutri=target_nutris[0]
    else:
        remaining_nutri=remaining_nutri[-1]

    return remaining_nutri

def interpolation(scale_use:bool, weight:float|int)->float:
    """
    Function that interpolates real weight to measured weight and vica-versa.
    :param scale_use: whether scale was used for weight
    :param weight: the weight to be converted 
    :return: the converted weight
    """

    scale_objects=load_objects("weight conversion", False)
    scale_object_names = [i.name for i in scale_objects]
    while "real" not in scale_object_names or len(scale_objects)<2:
        print(f"Measured and/or real data missing!")
        scale_objects=add_object(scale_objects, "weight conversion")
            

    real_index = scale_object_names.index("real")
    real = [getattr(scale_objects[real_index], i) for i in scale_objects[real_index].attributes if i != "name"]
    real.sort()
    if len(scale_objects) == 2:
        scale_objects.pop(real_index)
        measure = [getattr(scale_objects[0],i) for i in scale_objects[0].attributes if i!="name"]
        measure.sort()
    
    else:
        help=1
        while True:
            measure_name=input("Name of the measured data: ").strip()
            if measure_name.lower()=="help" and help==1:
                help-=1
                for i in scale_object_names:
                    print(i)
            elif measure_name.lower()==back_to_main:
                return main()
            elif measure_name not in scale_object_names:
                print(f"{measure_name} is not in the measurement database!")
            else:
                break
        measure_index = scale_object_names.index(measure_name)
        measure=[getattr(scale_objects[measure_index], i) for i in scale_objects[measure_index].attributes if i != "name"]
        measure.sort()
            
    if scale_use==True:
        if weight>max(measure):
            return weight
        else:
            for i in range(0,len(measure)):
                if measure[i]>=weight:
                    break
            i=i-1
            conversion=real[i]+((weight-measure[i])/(measure[i+1]-measure[i]))*((real[i+1]-real[i]))
    else:
        if weight>max(real):
            return weight
        else:
            for i in range(0,len(real)):
                if real[i]>=weight:
                    break
            i=i-1
            conversion=measure[i]+((weight-real[i])/(real[i+1]-real[i]))*((measure[i+1]-measure[i]))
    return conversion

def main():
    """
    Use cases of the programme.
    :return:
    """
    while True:
        try:
            task = int(input((
                "What would you like to do?\n"
                "\n"
                "\t0 = Record consumption\n"
                "\t1 = Record a dish\n"
                "\t2 = Add a new object\n"
                "\t3 = Modify an object\n"
                "\t4 = Delete an object\n"
                "\t5 = Add new product from USDA database\n"
                "\n"
                "Selected option: "
            )).strip())

        except ValueError:
            print("Only integers between 0-5 accepted!")
            task = -1

        if task in range(0, 6):
            break

    if task == 0:

        products = load_objects("product")

        meal = Nutrients()

        remaining_nutri = get_remaining_nutri()

        use = product_use_from_file(products)

        measure = input("Did you use scale? ").strip().lower()

        if measure==back_to_main:
            return main()

        elif measure in yes_answer:
            measure = True

        converted_measure = [0] * len(use)

        if measure == True:
            for i in range(0, len(use)):
                converted_measure[i] = interpolation(True, use[i][1])
        else:
            for i in range(0, len(use)):
                converted_measure[i] = interpolation(False, use[i][1])

        for i, k in zip(use, converted_measure):
            if measure == True:  
                for j in meal.attributes:
                    setattr(meal, j, getattr(meal, j) + getattr(i[0].nutri, j) * (k / i[0].amount))
                to_print = f"Consumption after scale measured {i[1]} g (in reality: {k} g) from {i[0].name}:"

            else:  
                for j in meal.attributes:
                    setattr(meal, j, getattr(meal, j) + getattr(i[0].nutri, j) * (i[1] / i[0].amount))
                to_print = f"Consumption after real {i[1]} g (on scale: {k} g) from {i[0].name}:"

            for j in meal.attributes:
                if j !="kCal":
                    to_print += f"\n\t{j}: {getattr(meal, j)} g"
                else:
                    to_print += f"\n\t{j}: {getattr(meal, j)}"

            print(to_print)
        for j in meal.attributes:
            setattr(remaining_nutri.nutri, j, getattr(remaining_nutri.nutri, j) - getattr(meal, j))

        remaining_nutri.name=str(datetime.datetime.today())

        to_print = "Remaining nutri for today: "

        for j in remaining_nutri.nutri.attributes:
            if j != "kCal":
                to_print += f"\n\t{j}: {getattr(remaining_nutri.nutri, j)} g"
            else:
                to_print += f"\n\t{j}: {getattr(remaining_nutri.nutri, j)}"

        print(to_print)

        write_objects_to_file([remaining_nutri], "remaining nutri",
                              "a", True, "\t")
        return main()

    if task == 1:

        products = load_objects("product")
        pots = load_objects("pot")
        pot_names=[i.name for i in pots]
        product_names=[i.name for i in products]
        meal=Nutrients()
        use = product_use_from_file(products)

        help=1
        while True:
            dish_name=input("Name of the cooked dish: ").strip()
            if dish_name.lower()=="help" and help==1:
                help-=1
                for i in product_names:
                    print(i)
            elif dish_name.lower()==back_to_main:
                return main()
            elif dish_name.lower() in product_names+[""]:
                print(f"{dish_name} already in product database, or empty input!")
            else:
                break

        
        measure = input("Did you use scale? ").strip().lower()

        if measure==back_to_main:
            return main()

        elif measure in yes_answer:
            measure = True

        help=1
        while True:
            pot=input("Name of the pot you used: ").strip()
            if pot.lower()=="help" and help==1:
                help-=1
                for i in pot_names:
                    print(i)
            elif pot.lower()==back_to_main:
                return main()
            elif pot.lower() in ("none",""):
                pot_weight=0
                break
            elif pot.lower() not in pot_names:
                print(f"{pot} is not in pot database!")
            else:
                pot_weight=pots[pot_names.index(pot)].weight
                break

        while True:
            final_weight=input("Final weight of dish (with pot): ").strip()
            if final_weight.lower()==back_to_main:
                return main()
            else:
                try:
                    final_weight=float(final_weight)
                    break
                except ValueError:
                    print("Weight parameter has to be a number!")


        converted_measure = [0] * len(use)

        if measure == True:
            for i in range(0, len(use)):
                converted_measure[i] = interpolation(True, use[i][1])
        else:
            for i in range(0, len(use)):
                converted_measure[i] = interpolation(False, use[i][1])

        for i, k in zip(use, converted_measure):
            if measure == True:  
                for j in meal.attributes:
                    setattr(meal, j, getattr(meal, j) + (getattr(i[0].nutri, j) * (k / i[0].amount))/(final_weight-pot_weight)*100)
                to_print = f"Nutri per 100 g, after adding scale measured {i[1]} g (in reality: {k} g) from {i[0].name} ingredient:"

            else:  
                for j in meal.attributes:
                    setattr(meal, j, getattr(meal, j) + (getattr(i[0].nutri, j) * (i[1] / i[0].amount))/(final_weight-pot_weight)*100)
                to_print = f"Nutri per 100 g, after adding real {i[1]} g (on scale: {k} g) from {i[0].name} ingredient:"

            for j in meal.attributes:
                if j !="kCal":
                    to_print += f"\n\t{j}: {getattr(meal, j)} g"
                else:
                    to_print += f"\n\t{j}: {getattr(meal, j)}"

            print(to_print)

        write_objects_to_file([Product(dish_name,meal,"diet calculator",100 )], "product","a",True)

        return main()

    if task == 2:  
        help=1
        valid_objects=object_classes.keys()
        while True:
            obj=input("To which database do you want to add object? ").strip().lower()
            if obj=="help" and help==1:
                help -= 1
                for i in valid_objects:
                    print(i)
            elif obj==back_to_main:
                return  main()
            elif obj not in valid_objects:
                print(f"There is no {obj} database!")
            else:
                break
        objects=load_objects(obj)
        objects=add_object(objects,obj)
        write_objects_to_file(objects,obj)
        return main()

    if task == 3: 
        help = 1
        valid_objects = object_classes.keys()
        while True:
            obj = input("In which database do you want modify object? ").strip().lower()
            if obj == "help" and help == 1:
                help -= 1
                for i in valid_objects:
                    print(i)
            elif obj == back_to_main:
                return main()
            elif obj not in valid_objects:
                print(f"There is no {obj} database!")
            else:
                break
        objects = load_objects(obj)
        objects = modify_object(objects, obj)
        write_objects_to_file(objects, obj)
        return main()

    if task == 4:  
        help = 1
        valid_objects = object_classes.keys()
        while True:
            obj = input("In which database do you want delete object? ").strip().lower()
            if obj == "help" and help == 1:
                help -= 1
                for i in valid_objects:
                    print(i)
            elif obj == back_to_main:
                return main()
            elif obj not in valid_objects:
                print(f"There is no {obj} database!")
            else:
                break
        objects = load_objects(obj)
        objects = delete_object(objects, obj)
        write_objects_to_file(objects, obj)
        return main()

    if task == 5:
        help = 1
        valid_dbs = usda_db.keys()
        while True:
            dbase = input("Database(s) you want to search for product (separated by SPACE): ").strip().lower().split(" ")
            if "help" in dbase and help == 1:
                help-=1
                for i in usda_db:
                    print(f"\t{i} : {usda_db[i]}")
            elif back_to_main in dbase:
                return main()
            elif any(i not in valid_dbs for i in dbase):
                print(f"Invalid database name detected!")
            else:
                break

        for i in range(0,len(dbase)):
            dbase[i]=usda_db[dbase[i]]

        help = 1
        while True:
            keyword = rf'{input("Keyword(s) for searching the database(s): ").strip()}'
            if keyword.lower() == "help" and help == 1:
                help-=1
                for i in usda_kw:
                    print(f"\t{i} : {usda_kw[i]}")
            elif keyword.lower()==back_to_main:
                return main()
            else:
                break

        require_all_words=input("Do you require all the given words in the matches? ").strip().lower()
        if require_all_words==back_to_main:
            return main()
        elif require_all_words in yes_answer:
            require_all_words=True
        else:
            require_all_words=False

        list_usda_items(dbase, keyword, require_all_words)  

        while True:
            try:
                chosen_product=[int(i) for i in input("ID(s) of the item(s) you want to add to the product database (separated by SPACE): ").strip().split(" ")]
                if back_to_main in chosen_product:
                    return main()
                else:
                    break
            except ValueError:
                print("ID(s) must be numbers!")

        write_objects_to_file(get_items_from_usda(chosen_product), "product", "a", True)

        return main()




if __name__=="__main__":
    main()
            












