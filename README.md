# Smart Shower Project

## Wireless Sensor Networks


## Links

- [AWSIoTPythonSDK](https://github.com/aws/aws-iot-device-sdk-python)
- [Amazon Web Services](https://aws.amazon.com/)

## Front-end iOS app

The application is written to be able to run on any supported iOS phone in vertical or horizontal orientation. When launched the app connects to AWSIoT allowing the user to quickly interface with their shower. Upon closing the app, user actions are retained, such as if the shower was started and at what temperature are stored on the iOS device, so if launched again the app can give the user appropriate interface. The application does continue to run in the background, communicating with AWSIoT but is unable to send push notifications due to Apple's requirement of a developer account to further develop and test the feature. If a message was received there is still an on screen notification if the application is running in the foreground, giving the user information and actions to handle the notification.

### Built with

- [XCode 12](https://developer.apple.com/xcode/)
- [Swift](https://developer.apple.com/swift/)
- [CocaPods](https://cocoapods.org)

### Getting Started

Running the iOS application requires a Mac device with version 10.15 Catalina or 11 Big Sur (preferred).

#### Prerequisites

- Download and install [Xcode 12](https://developer.apple.com/xcode/)
- Install CocaPods
  - CocoaPods is built with Ruby and is installable with the default Ruby available on macOS. It is recommend you use the default ruby.
  - Using the default Ruby install can require you to use `sudo` when installing gems. Further installation instructions are in [the guides](https://guides.cocoapods.org/using/getting-started.html#getting-started).

        $ sudo gem install cocoapods

- In your project directory (the directory where your `*.xcodeproj` file is), run the following to create a Podfile in your project. `smartShower/smartShowerApp`

        $ pod init
        $ pod install --repo-update

### Running

To open your project, open the newly generated `*.xcworkspace` file in your project's directory with XCode. You can do this by issuing the following comman d in your project folder:

    $ xed .

**Note**: Do **NOT** use `*.xcodeproj`. If you open up a project file instead of a workspace, you may receive the following error:

    ld: library not found for -lPods-AWSCore
    clang: error: linker command failed with exit code 1 (use -v to see invocation)

Now you can build and run the project, also change the device if you'd like.
### Acknowledgements

- [AWS SDK for iOS](https://github.com/aws-amplify/aws-sdk-ios)
- [AWSIoT IOS Guide](https://medium.com/swlh/connect-an-ios-app-to-aws-iot-fc99d5a9562f)

## Shower Controller

The shower controller is a python script that comunicates with the rest of the Smart Shower system using AWS IoT topics. It also communicates with a servo using PWM and a temperature sensor using the 1-Wire protocol. Receipt of a control topic with an float value will start the shower and attempt to reach that temperature. Receipt of a control topic with "stop" will turn the shower off. The script will publish a ready topic when the shower has reached +/-0.5*F from the desired temperature.

Within the `showerController/` folder there a four files. The `controller-demo<#>.py` scripts are the main controller scripts where the number refers to the demo the script was used for. There is also a `stop-shower.py` script with just sends the servo commands to turn off the shower.

## Machine Learning

The machine learning directory in this project contains the `shower_ec2_pubsub.py` script.  This script acts as the server for the smart shower system.  It runs on a AWS EC2 T2 Micro instance.  This script communicates to the mobile application and the shower controller.  It relays commands from the application to the shower and vice versa.

Another script that works with the `shower_ec2_pubsub.py` is the `test_binning_kbinsdis.py` script.  This script performs data analysis of both the temperature and time data. The two txt files, `temperatures.txt` and `time.txt,` are written to at runtime.  That data is then saved and used to perform habit recognition on both the time the user takes a shower and how hot they prefer it.

### Built with

- [Python3](https://www.python.org)

### Getting Started

With a terminal window open in the `showerController/` folder in this repository, run the command `python3 controller-demo3.py` to start the latest shower controller script. The script will take a few seconds to initialize the topics and will then be ready to receive topics and interface with the servo and temperature sensor.

With another terminal window open please connect to the AWS EC2 instance.  The machine learning directory exists on the server and mirrors what we have in our repo.  To run locally open a terminal and navigate the to `machineLearning/` folder.  Once inside this directory, run the command `python3 shower_ec2_pubsub.py` to start the server.  The script will start printing `Determining if notification should be sent.`  This means that it is waiting for the start command from the application and running habit recognition of past data to determine if a push notification should be sent to the application to take a shower.

#### Prerequisites

- A [Raspberry Pi 3B+](https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/) with an [Adafruit Servo Hat](https://www.adafruit.com/product/2327)
- A DS18B20 digital temperature sensor (preferably with [waterproof enclosure](https://www.adafruit.com/product/381))
- A servo (preferably [high torque and waterproof](https://www.amazon.com/ANNIMOS-Coreless-Stainless-Waterproof-Standard/dp/B07SWST8D6))
- The following Python libraries:
  - [AWSIoTPythonSDK](https://github.com/aws/aws-iot-device-sdk-python)

        pip3 install AWSIoTPythonSDK

  - [adafruit_servokit](https://circuitpython.readthedocs.io/projects/servokit/en/latest/)

        pip3 install adafruit_servokit

  - [simple_pid](https://simple-pid.readthedocs.io/en/latest/)

        pip3 install simple_pid

### Acknowledgements

- [Adafruit Servo HAT Guide](https://learn.adafruit.com/adafruit-16-channel-pwm-servo-hat-for-raspberry-pi)
- [Adafruit DS18B20 Guide](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing)
- The Python library documentation linked in the "Prerequisites" section