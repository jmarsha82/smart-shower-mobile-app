//
//  ShowerPersistence+CoreDataProperties.swift
//  smartShowerApp
//
//

import Foundation
import CoreData


extension ShowerPersistence {

    @nonobjc public class func fetchRequest() -> NSFetchRequest<ShowerPersistence> {
        return NSFetchRequest<ShowerPersistence>(entityName: "ShowerPersistence")
    }

    @NSManaged public var pickedTemp: Int32
    @NSManaged public var showerOn: Bool

}

extension ShowerPersistence : Identifiable {

}
