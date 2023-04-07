//
//  ShowerPersistence+CoreDataClass.swift
//  smartShowerApp
//
//

import Foundation
import CoreData

@objc(ShowerPersistence)
public class ShowerPersistence: NSManagedObject {

    func initDefaults(){
        self.showerOn = false
        self.pickedTemp = 0
    }

}
