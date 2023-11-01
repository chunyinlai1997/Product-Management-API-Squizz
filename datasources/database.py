import logging
import datetime
import random
import time
import pymysql
from typing import Tuple
from werkzeug.security import generate_password_hash, check_password_hash
import json

logger = logging.getLogger(__name__)

class Database:

    def __init__(self):
        host = "52.68.78.115"
        user = "squizz"
        password = "squizz"
        charSet = "utf8mb4"
        db = "squizz_app"
        
        self.con = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            read_timeout=None, 
            write_timeout=None,
            charset=charSet
        )
        self.cur = self.con.cursor()
        self.con.get_autocommit()

    def run_query(self, query: str, values: list, commit: bool = False):
        """
        This method runs MYSQL commands and return the result retrieved from database

        Args:
            query - a string of MYSQL command to be executed
            values - a list of values for the query
            commit - requries to commit after execution
        """
        if not self.con.open :
            self.con.ping(reconnect=True)
            logger.info("reconnecting to the database")
        try:
            self.cur.execute(query, values)
            if commit:
                self.con.commit()
            if not self.cur.rowcount:
                return None
            else:
                return self.cur.fetchall()
        except Exception as e:
            logger.error("Could exceute the query" , e)
            return None

    def validate_username_password(self, username: str, password: str) -> str:
        """
        This method retrieves the customer org id and password based on the username and vaidate the user's identity.

        Args:
            username - user's input
            password - hashed password string
        """
        query = "SELECT customers_org_id, passwd FROM userinfo WHERE username=%s"
        values = [username]
        result = self.run_query(query, values, False)
        if result is not None:
            result = result[0]
            if check_password_hash(result['passwd'], password):
                return result['customers_org_id']
            else:
                logger.info("wrong username or password")
                return None
        else:
            logger.error("Could not validate username password")
            return None

    def retrieve_api_key_pw(self, org_id: str) -> Tuple[str, str]:
        """
        This method retrieves the api key and password based on the user's organsisation ID

        Args:
            org_id - the orginisation ID of the user
        """
        query = "SELECT api_org_key, api_org_pw FROM customers WHERE org_id=%s"
        values = [org_id]
        result = self.run_query(query, values, False)
        if result is not None:
            result = result[0]
            return result["api_org_key"], result["api_org_pw"]
        else:
            logger.error("Could not retrieve api key and pw")
            return None, None
        
    def store_session(self, login_session: str, org_id: str):
        """
        This method strores the login session to the database

        Args:
            login_session - the session string
            org_id - the orginisation ID of the user
        """
        query = "INSERT INTO session (id, customers_org_id) VALUES (%s, %s)"
        values = [login_session, org_id]
        result = self.run_query(query, values, True)

    def validate_session(self, login_session, org_id: str):
        """
        This method validates whether login_session exists already in the database

        Args:
            login_session - the session string
            org_id - the orginisation ID of the user
        """
        query = "SELECT count(*) as num FROM session WHERE id=%s and customers_org_id=%s"
        values = [login_session, org_id]
        result = self.run_query(query, values, False)
        if result is not None and result[0]['num'] > 0:
            return True
        else:
            logger.info("No valid session")
            return False

    def remove_session(self, login_session: str):
        """
        This method deletes the login session record in the database

        Args:
            login_session - the session string
        """
        query = "DELETE FROM session WHERE id = %s"
        values = [login_session]
        result = self.run_query(query, values, True)
        logger.info("Removed session")

    def create_user(self, username: str, password: str):
        #temporary function
        org_id = "11EA64D91C6E8F70A23EB6800B5BCB6D"
        hpassword = generate_password_hash(password)
        query = "INSERT INTO userinfo (customers_org_id, username, passwd) VALUES (%s,%s,%s)"
        values = [org_id, username, hpassword]
        result = self.run_query(query, values, True)
        logger.info("Cretaed user")


    def store_product(self, jsonValues):
        value_not_inserted = 0
        value_inserted = 0
        insert_query = "INSERT INTO products(id, keyTaxCodeID, supplierAccountCode, " \
                       "productCode, keyProductID, barcode, barcodeInner, name," \
                       "description1, keySellUnitID, width, height, stockQuantity," \
                       "stockLowQuantity, isPriceTaxInclusive, isKitted, kitProductsSetPrice, internalID)" \
                       " VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s,%s,%s,%s) "

        PjSAS_id = "11EA0FDB9AC9C3B09BE36AF3476460FC"
        failedToStore = []
        for dataRecord in jsonValues:
            try:
                values = [
                    dataRecord['keyProductID'] + PjSAS_id,
                    dataRecord['keyTaxcodeID'], PjSAS_id, dataRecord['productCode'],
                    dataRecord['keyProductID'], dataRecord['barcode'],
                    dataRecord['barcodeInner'], dataRecord['name'],
                    dataRecord['description1'], dataRecord['keySellUnitID'],
                    dataRecord['width'], dataRecord['height'],
                    dataRecord['stockQuantity'],dataRecord['stockLowQuantity'],
                    dataRecord['isPriceTaxInclusive'],dataRecord['isKitted'],
                    dataRecord['kitProductsSetPrice'],dataRecord['internalID']
                ]
                self.run_query(insert_query, values, True)

            except Exception as e:
                logger.error("exception", e)
                failedToStore.append(dataRecord['keyProductID'] + "error: " +str(e))

        logger.info('completed store_product')
        result = {'status': "success",'data':{'failed': failedToStore}, 'message': "successfully stored products"}
        return result

    
    def store_product_price(self, jsonValue):
        insert_query = "INSERT INTO squizz_app.price_level(products_id, keySellUnitID, "\
                      "referenceId, referenceType, price, keyProductID, date_time)"\
                      " VALUES (%s, %s, %s, %s, %s, %s, %s)"
        search_query = "SELECT * FROM products WHERE keyProductID=%s"
        PjSAS_id = "11EA0FDB9AC9C3B09BE36AF3476460FC"
        failedToStore = []
        for dataRecord in jsonValue:
            #print(dataRecord)
            key_product_id = dataRecord['keyProductID']
            # First, search in the product table to check whether this product exsts.
            # If not, skip this record and continue. Otherwise, it may cause foreign key
            # constraint issue.
            product_record = None
            try:
                #self.cur.execute(search_query, key_product_id)
                #_, product_record = self.cur.fetchall()
                product_record = self.run_query(search_query, key_product_id, False)
            except Exception as e:
                logger.error('Exception occurred when searching for product record in store_product_level method.', e)

            if product_record is not None:
                # Since we already checked the existence of the product, we could do the insertion.
                try:
                    now = datetime.datetime.now()
                    dateTime = now.strftime("%Y-%m-%d  %H:%M:%S")
                    values = [
                        dataRecord['keyProductID'] + PjSAS_id, dataRecord['keySellUnitID'],
                        dataRecord['referenceID'], dataRecord['referenceType'],
                        dataRecord['price'], dataRecord['keyProductID'], dateTime
                    ]
                    self.run_query(insert_query, values, True)
                except Exception as e:
                    logger.error("Exception", e)
                    failedToStore.append(dataRecord['keyProductID']+ "error: " + str(e))

            else:
                failedToStore.append(dataRecord['keyProductID'] + "error:" + "product does not exist")

        logger.info('completed store_product_price')
        result = {'status': "success", 'data': {'failed':failedToStore}, 'message': "successfully stored price of products"}
        return result


    def get_barcode_value(self, barcode):
        sql_query = "SELECT * FROM squizz_app.products RIGHT JOIN squizz_app.price_level ON squizz_app.products.id=squizz_app.price_level.products_id " \
                    "WHERE squizz_app.products.barcode = %s"
        values = self.run_query(sql_query % barcode,[], False)
        print(values)
        try:
            if values is not None:
                result = {'status': "success", 'data': {'productname': values[0]['name'], 'keyProductCode': values[0]['keyProductID'], 'price': values[0]['price'],'filename':values[0]['filename'],
                                                        'uri_small':values[0]['uri_small'],'uri_medium':values[0]['uri_medium'],'uri_large':values[0]['uri_large'], 'productCode': values[0]['productCode']}, 
                                                        'message': "successfully retrieved price"}
                return result
            else:
                result = {'status': "error",'data': 'null', 'Message': "No data found"}
                return result
        except Exception as e:
            result = {'status': "error",'data':'null', 'Message': str(e)}
            return result

    def update_product(self, json_values):
        """
        This method retrieves the product data from SQUIZZ API every 24 hour, it then checks with the local database.
        If they are not identical, it will update the product information to the latest one.

        Args:
            json_values - the json records of product information retrieved through SQUIZZ API
        """
        value_not_inserted = 0
        value_inserted = 0

        # the primary keys of the product table is 'id' which is automatically generated by local database, can not
        # included in the json_value. Therefore, we use the 'keyProductID' to do the query
        PjSAS_id = "11EA0FDB9AC9C3B09BE36AF3476460FC"
        failedToStore = []
        for data_record in json_values:
            key_product_id = data_record['keyProductID']
            search_query = "SELECT id, keyTaxCodeID, supplierAccountCode, " \
                           "keyProductID, barcode, barcodeInner, name," \
                           "description1, keySellUnitID, width, height, " \
                           "stockQuantity, stockLowQuantity, isPriceTaxInclusive, " \
                           "isKitted, kitProductsSetPrice, internalID " \
                           "FROM products " \
                           "Where keyProductID=%s"
            result = None
            try:
                # TODO: discuss later, theoretically, there ought to be only one record. Attention: the record retrieved below
                result_all = self.run_query(search_query, key_product_id, False)
                result = result_all[0]
            except Exception as e:
                value_not_inserted += 1
                logger.error('Exception occurred when searching for record in update product session', e)
                failedToStore.append(data_record['keyProductID'] + "error:" + "product does not exist")

            if result is None:
                logger.error('Get no corresponding record, insert a new record.')
                # TODO: insert a new record, how to handle the auto-increased id in local db,
                #  currently we use store_product method
                json_value = [data_record]
                self.store_product(json_value)
                value_inserted += 1

            else:
                # data_record['name'] = data_record['name'].replace("'", "''")
                # data_record['description1'] = data_record['description1'].replace("'", "''")
                latest_record = [
                    data_record['keyProductID'] + PjSAS_id,
                    data_record['keyTaxcodeID'],
                    PjSAS_id,
                    data_record['keyProductID'],
                    data_record['barcode'],
                    data_record['barcodeInner'],
                    data_record['name'],
                    data_record['description1'],
                    data_record['keySellUnitID'],
                    data_record['width'],
                    data_record['height'],
                    data_record['stockQuantity'],
                    data_record['stockLowQuantity'],
                    data_record['isPriceTaxInclusive'],
                    data_record['isKitted'],
                    data_record['kitProductsSetPrice'],
                    data_record['internalID'],
                    data_record['productCode']
                ]

                # TODO: Currently, for simplicity, we just update the entire record once it is inconsistent with the
                #  latest record
                latest_record.append(key_product_id)
                # latest_record = tuple(latest_record)
                update_query = "UPDATE products " \
                               "SET id = %s, keyTaxCodeID=%s, supplierAccountCode=%s," \
                               "keyProductID=%s, barcode=%s, barcodeInner=%s, name=%s," \
                               "description1=%s, keySellUnitID=%s, width=%s, height=%s," \
                               "stockQuantity=%s, stockLowQuantity=%s, isPriceTaxInclusive=%s," \
                               "isKitted=%s, kitProductsSetPrice=%s, internalID=%s, productCode=%s " \
                               "WHERE keyProductID=%s"

                try:
                    self.run_query(update_query, latest_record, True)
                    value_inserted += 1
                except Exception as e:
                    self.con.rollback()
                    logger.error('Exception occurred when updating product table', e)
                    value_not_inserted += 1
                    failedToStore.append(data_record['keyProductID'] + "error:" + "error occured while updating: " + str(e))

        self.con.close()
        logger.info('This is the value updated: %d' % value_inserted)
        logger.info('This is the value not updated: %d' % value_not_inserted)
        result = {'status': "success", 'data': {'failed':failedToStore}, 'message': "successfully updated products"}
        return result
    logger.info('completed update_product')

    def update_product_price(self, json_values):
        """
        This methods updates price_level table every 24 hours.
        It compares the retrieved data with data in the local database. If they are identical, it only updates datetime;
        otherwise, the entire record will be updated.

        Args:
             json_values - the json records of product price retrieved through SQUIZZ API
        """
        PjSAS_id = "11EA0FDB9AC9C3B09BE36AF3476460FC"
        failedToStore = []
        for data_record in json_values:
            key_product_id = data_record['keyProductID']
            search_query = "SELECT products_id, keySellUnitID, "\
                           "referenceId, referenceType, price, date_time " \
                           "FROM price_level " \
                           "WHERE keyProductID = %s"
            try:
                result_all = self.run_query(search_query, key_product_id, False)
                if result_all is None:
                    json_value = [data_record]
                    self.store_product_price(json_value)
                else:
                    current_time = datetime.datetime.now()
                    date_time = current_time.strftime("%Y-%m-%d  %H:%M:%S")
                    latest_values = [
                        data_record['keyProductID'] + PjSAS_id,
                        data_record['keySellUnitID'],
                        data_record['referenceID'],
                        data_record['referenceType'],
                        data_record['price'],
                        date_time,
                        data_record['keyProductID']
                    ]

                    update_query = "UPDATE price_level " \
                            "SET products_id=%s, keySellUnitID=%s, referenceId=%s, " \
                            "referenceType=%s, price= %s, date_time=%s " \
                            "WHERE keyProductID = %s"
                    try:
                        self.run_query(update_query, latest_values, True)
                    except Exception as e:
                        self.con.rollback()
                        logger.error('Exception occurred when updating the latest price info', e)
                        failedToStore.append(data_record['keyProductID'] + "error:" + "failed to update price")
            except Exception as e:
                logger.error('Exception occurred when search price in price_level', e)
                failedToStore.append(data_record['keyProductID'] + "error:" + "failed to update price")
                # self.con.close()
        result = {'status': "success", 'data': {'failed':failedToStore}, 'message': "successfully updated price of products"}
        return result
    logger.info('completed update_product_price')
    
    def purchase(self, session_id, squizzRep, purchaseList):
        """
        This methods will insert purchase table and lines tables in the database

        Args:
             session_id: squizz session id for submit purchase
             squizzRep: response from SQUIZZ of whether the purchase has been proceeded properly
             purchaseList: products listed in the purchase
        """
        now = datetime.datetime.now()
        dateTime = now.strftime("%Y-%m-%d  %H:%M:%S")
        PjSAS_id = "11EA0FDB9AC9C3B09BE36AF3476460FC"

        keyPurchaseOrderID = purchaseList['keyPurchaseOrderID']
        supplierAccountCode = PjSAS_id
        createdDate = dateTime
        status = squizzRep
        failedToStore = []

        # search the user organization ID based on session ID from seesion table
        search_query = "SELECT customers_org_id FROM squizz_app.session WHERE id=%s"
        try:
            tempCustomer = self.run_query(search_query, [session_id], False)
            # get cutomer organization ID
            customerAccountCode = tempCustomer[0]["customers_org_id"]
        except Exception as e:
            self.con.rollback()
            logger.error('Session not found', e)
        # Insert the purchase records. lines are store as strings in this table for fast lookup.
        lines = purchaseList["lines"]
        for i in range(0, len(lines)):
            keyProductID = lines[i]["productId"]
            uri_search_query = "SELECT * FROM squizz_app.products WHERE keyProductID=%s"
            try:
                uri = self.run_query(uri_search_query, [keyProductID], False)
                lines[i]['uri_small'] = uri[0]['uri_small']
                lines[i]['uri_medium'] = uri[0]['uri_medium']
                lines[i]['uri_large'] = uri[0]['uri_large']
            except Exception as e:
                self.con.rollback()
                logger.error('URI search error', e)

        insert_query = "INSERT INTO squizz_app.purchase(keyPurchaseOrderID, supplierAccountCode, "\
                      "customerAccountCode, keySupplierAccountID, createdDate, bill_status, "\
                      "deliveryContact, deliveryAddress1, deliveryAddress2, deliveryAddress3, session_id, line)"\
                      " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = [
            keyPurchaseOrderID, supplierAccountCode, customerAccountCode, supplierAccountCode,
            createdDate, status, 
            "+6144433332222", "Unit 5", "22 Bourkie Street", "Melbourne",  # Hard code variables
            session_id, str(lines)
        ]
        try:
            self.run_query(insert_query, values, True)
        except Exception as e:
            self.con.rollback()
            logger.error('Exception occurred when insert new purchase order', e)
        
        # insert table 'lines'
        try:
            for line in purchaseList["lines"]:
                # insertion query for table 'lines'
                insert_query = "INSERT INTO squizz_app.lines(lineType, purchase_keyPurchaseOrderID, keyProductID,"\
                               "quantity, priceTotalExTax, products_id) VALUES (%s, %s, %s, %s, %s, %s)"
                values = [
                    line['lineType'], keyPurchaseOrderID, line['productId'], line['quantity'],
                    line['priceTotalExTax'], line['productId'] + PjSAS_id
                ]
                try:
                    self.run_query(insert_query, values, True)
                except Exception as e:
                    self.con.rollback()
                    failedToStore.append(line['productCode'] + "error:" + "failed to store the purchase of order")

        except Exception as e:
            logger.error('Exception occurred when insert new purchase order', e)
            result = {'status': "error", 'data': 'null',
                      'Message': 'Exception occurred when adding purchase order'}
            return result

        # Only 'SERVER_SUCCESS' means SQUIZZ accept the purchase, others are negative
        result = {'status': "success", 'data': {'puchaseID':keyPurchaseOrderID}, 'message': "successfully added the purchase orders"}
        return result

        
    
    def history_order(self, session_id, date_time):
        """
            This method will return the last 15 history records from the search time
            Args: 
                session_id: session ID of current user.
                data_time: start time of searching
        """
        customer_search_query = "SELECT customers_org_id FROM squizz_app.session WHERE id=%s"
        try:
            tempCustomer = self.run_query(customer_search_query, [session_id], False)
            customerAccountCode = tempCustomer[0]["customers_org_id"] # get cutomer organization ID
        except Exception as e:
            self.con.rollback()
            logger.error('Session not found', e)
            result = {'status': "error", 'data': 'null','Message': 'Session invalid, please login again'}
            return result
        # query for searching the history orders
        order_search_query = "SELECT keyPurchaseOrderID,createdDate,line," \
                             "bill_status FROM squizz_app.purchase WHERE " \
                             "customerAccountCode=%s and createdDate<=%s ORDER BY createdDate DESC LIMIT 15"
        try:
            order_info = self.run_query(order_search_query, [customerAccountCode, date_time], False)
            if order_info is not None:
                for i in range(0, len(order_info)):
                    order_info[i]['line'] = list(eval(order_info[i]['line']))
                result = {'status': "success", 'data': {'history_orders': order_info}, 'message': "successfully retrieved history order"}
                return result
            else:
                result = {'status': "success", 'data': 'null', 'message': "Success, but no data found!"}
                return result
        except Exception as e:
            logger.error('Order searching failure:', e)
            result = {'status': "error", 'data': 'null','Message': 'Exception occurred when retrieving history order' +str(e)}
            return result
