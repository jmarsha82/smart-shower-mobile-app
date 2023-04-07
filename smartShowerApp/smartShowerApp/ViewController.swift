//
//  ViewController.swift
//

import UIKit
import AWSIoT
import UserNotifications

class ViewController: UIViewController
{
    @IBOutlet weak var temperaturePicker: UIPickerView!
    @IBOutlet weak var label: UILabel!
    @IBOutlet weak var startStopBtn: UIButton!

    let credentials = AWSCognitoCredentialsProvider(regionType:.USEast2, identityPoolId: IDENTITY_POOL_ID)
    var configuration : AWSServiceConfiguration?

    var pickerData: [String] = [String]()
    let TEMP_SYMBOL = "°"

    var showerPersistence:ShowerPersistence?

    /***Main method which get's called if app is opened for the first time*/
    override func viewDidLoad()
    {
        super.viewDidLoad()

        // Setting up AWS Service Config here (could not keep it as let for some reason
        configuration = AWSServiceConfiguration(region:.USEast2, credentialsProvider: credentials)

        // Make sure all the objects are created properly and are ready to go
        initAWSIoT()
        // Connect to aws if this is the users is launching the app from closed state
        connectToAWSIoT(clientId: CLIENT_ID)

        label.text = "Desired Shower Temperature " + TEMP_SYMBOL + "F"
        // Do any additional setup after loading the view.
        for number in 60...105
        {
            pickerData.append(String(number) + TEMP_SYMBOL)
        }

        // Connect data to the view
        self.temperaturePicker.delegate = self
        self.temperaturePicker.dataSource = self

        // Getting saved data of the iphone to see if the user started the shower or not
        if PersistenceHelper.getSavedPetStoreData().count > 0
        {
            showerPersistence = PersistenceHelper.getSavedPetStoreData()[0]
        }
        else // if this is the first opening the app
        {
            showerPersistence = ShowerPersistence.init(context: PersistenceHelper.context)
            showerPersistence?.initDefaults()
        }
        temperaturePicker.selectRow(Int(showerPersistence?.pickedTemp ?? 0), inComponent: 0, animated: true)
        // Update the button to be start or stop
        changeBtn()
    }

    // MARK: - AWS IoT
    func initAWSIoT()
    {
        // Initialising AWS IoT And IoT DataManager
        AWSIoT.register(with: configuration!, forKey: AWS_IOT_MANAGER_KEY)  // Same configuration var as above
        let iotEndPoint = AWSEndpoint(urlString: IOT_ENDPOINT) // Access from AWS IoT Core --> Settings
        let iotDataConfiguration = AWSServiceConfiguration(region: .USEast2,     // Use AWS typedef .Region
                                                           endpoint: iotEndPoint,
                                                           credentialsProvider: credentials)  // credentials is the same var as created above
        AWSIoTDataManager.register(with: iotDataConfiguration!, forKey: AWS_IOT_DATA_MANAGER_KEY)
    }

    func connectToAWSIoT(clientId: String)
    {

        func mqttEventCallback(_ status: AWSIoTMQTTStatus )
        {
            switch status {
            case .connecting: print("Connecting to AWS IoT")
            case .connected:
                print("Connected to AWS IoT")
                registerSubscriptions()
            // Register subscriptions here
            // Publish a boot message if required
            case .connectionError: print("AWS IoT connection error")
            case .connectionRefused: print("AWS IoT connection refused")
            case .protocolError: print("AWS IoT protocol error")
            case .disconnected: print("AWS IoT disconnected")
            case .unknown: print("AWS IoT unknown state")
            default: print("Error - unknown MQTT state")
            }
        }

        // Ensure connection gets performed background thread (so as not to block the UI)
        DispatchQueue.global(qos: .background).async
        {
            do
            {
                print("Attempting to connect to IoT device gateway with ID = \(clientId)")
                let dataManager = AWSIoTDataManager(forKey: AWS_IOT_DATA_MANAGER_KEY)
                dataManager.connectUsingWebSocket(withClientId: clientId,
                                                  cleanSession: true,
                                                  statusCallback: mqttEventCallback)

            }
        }
    }

    /**After getting connected to the AWS IoT all subscriptions are registered to allow the app to communicate properly with backend*/
    func registerSubscriptions()
    {
        // Call back method, and topic subscribed to below need to be handled properly
        func messageReceived(payload: Data)
        {
            let payloadDictionary = jsonDataToDict(jsonData: payload)
            print("Message received: \(payloadDictionary)")
            // Handle message event here...
            // One type of status is ["status": true]
            if ((payloadDictionary["status"] != nil) == true)
            {
                showerReady() // Informing user shower is ready
            } // User needs to have suggested time
            else if (payloadDictionary["suggestedTime"] != nil && payloadDictionary["suggestedTemp"] != nil)
            {

                if let suggestedTime: String = payloadDictionary["suggestedTime"] as? String
                {
                    if var suggestedTemp: String = payloadDictionary["suggestedTemp"] as? String
                    {
                        let temp: Int? = Int(suggestedTemp)
                        if (temp != nil)
                        {
                            suggestedTemp = String(temp!)
                            suggestShower(suggestedTime: suggestedTime, suggestedTemp: suggestedTemp)
                        }
                        else{
                            print("failed to convert to in")
                        }
                    }
                    else{
                        print("Could not get suggested temp.")
                    }
                }
                else{
                    print ("Could not get suggested time.")
                }

            }
            else
            {
                print ("Error unknown payload.")
            }

        }

        // All topics I need to subscribe to
        let topicArray = [SHOWER_STATUS_TOPIC, SHOWER_NOTIFY]
        let dataManager = AWSIoTDataManager(forKey: AWS_IOT_DATA_MANAGER_KEY)

        for topic in topicArray {
            print("Registering subscription to => \(topic)")
            dataManager.subscribe(toTopic: topic,
                                  qoS: .messageDeliveryAttemptedAtLeastOnce,  // Set according to use case
                                  messageCallback: messageReceived) // Call back method defined above
        }
    }

    func jsonDataToDict(jsonData: Data?) -> Dictionary <String, Any>
    {
        // Converts data to dictionary or nil if error
        do {
            let jsonDict = try JSONSerialization.jsonObject(with: jsonData!, options: [])
            let convertedDict = jsonDict as! [String: Any]
            return convertedDict
        } catch {
            // Couldn't get JSON
            print(error.localizedDescription)
            return [:]
        }
    }

    func publishMessage(message: String!, topic: String!)
    {
        let dataManager = AWSIoTDataManager(forKey: AWS_IOT_DATA_MANAGER_KEY)
        dataManager.publishString(message, onTopic: topic, qoS: .messageDeliveryAttemptedAtLeastOnce) // Set QoS as needed
    }

    // MARK: - UI Manipulation
    func changeBtn()
    {
        if (showerPersistence?.showerOn ?? false)
        {
            startStopBtn.setTitle("Stop Shower", for: .normal)
            startStopBtn.backgroundColor = UIColor.red
        }
        else
        {
            startStopBtn.setTitle("Start Shower", for: .normal)
            startStopBtn.backgroundColor = UIColor.green
        }
    }

    @IBAction func startShowerBtn(_ sender: Any) {
        if !(showerPersistence?.showerOn ?? false)
        {
            startShower()
        }
        else
        {
            stopShower()
        }
    }

    func startShower()
    {
        let temp = pickerData[Int(self.showerPersistence!.pickedTemp)].replacingOccurrences(of: TEMP_SYMBOL, with: "")
        //\"command\": \"start\",
        publishMessage(message: "{\"temperature\": \"" + temp + "\" }", topic: SHOWER_START_STOP_TOPIC)
        showerPersistence?.showerOn = true
        PersistenceHelper.saveContext()
        changeBtn()
    }

    func stopShower()
    {
        publishMessage(message: "{\"temperature\": \"stop\" }", topic: SHOWER_START_STOP_TOPIC)
        showerPersistence?.showerOn = false
        PersistenceHelper.saveContext()
        changeBtn()
    }

    func showerReady()
    {
        DispatchQueue.main.async {
            let alertController = UIAlertController(title: "Shower Ready", message: "You can turn off the shower if you're not ready.", preferredStyle: .alert)
            let removeLocalNotificationAction = UIAlertAction(title: "Stop Shower", style: .default) { (action) in
                LocalNotificationManager.cancel()
                self.stopShower()
            }
            let cancelAction = UIAlertAction(title: "Close", style: .cancel) { (action) in }
            alertController.addAction(removeLocalNotificationAction)
            alertController.addAction(cancelAction)
            self.present(alertController, animated: true, completion: nil)
        }
    }

    func suggestShower(suggestedTime: String, suggestedTemp: String)
    {
        DispatchQueue.main.async {
            let alertController = UIAlertController(title: "Shower Suggestion", message: "You usually take a shower at " + suggestedTime + " at the temperature " + suggestedTemp + " would you like to start shower?", preferredStyle: .alert)
            let removeLocalNotificationAction = UIAlertAction(title: "Start Shower", style: .default) { (action) in
                let index = self.pickerData.firstIndex(of: suggestedTemp + self.TEMP_SYMBOL) ?? 40
                // Change the gui
                self.temperaturePicker.selectRow(index, inComponent: 0, animated: true)
                self.showerPersistence!.pickedTemp = Int32(index)
                self.startShower()
                LocalNotificationManager.cancel()
            }
            let cancelAction = UIAlertAction(title: "Close", style: .cancel) { (action) in }
            alertController.addAction(removeLocalNotificationAction)
            alertController.addAction(cancelAction)
            self.present(alertController, animated: true, completion: nil)
        }
    }
}



// MARK: - Temperature Picker
extension ViewController: UIPickerViewDelegate, UIPickerViewDataSource
{
    func numberOfComponents(in pickerView: UIPickerView) -> Int {
        // How many pikers do you want
        return 1
    }

    func pickerView(_ pickerView: UIPickerView, numberOfRowsInComponent component: Int) -> Int {
        return self.pickerData.count
    }

    func pickerView(_ pickerView: UIPickerView, didSelectRow row: Int, inComponent component: Int) {
        // get value
        self.showerPersistence?.pickedTemp = Int32(row)
        PersistenceHelper.saveContext()
    }

    func pickerView(_ pickerView: UIPickerView, titleForRow row: Int, forComponent component: Int) -> String? {
        self.showerPersistence?.pickedTemp = Int32(row)
        PersistenceHelper.saveContext()
        return pickerData[Int(self.showerPersistence!.pickedTemp)]
    }
}
