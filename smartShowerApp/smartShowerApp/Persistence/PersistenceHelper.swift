//
//  PersistenceHelper.swift
//  Virtual Pet
//

import Foundation
import CoreData
import os.log


/**
 Creating a static object seemed like the cleanest way to maintain all the auto generated code
 */
class PersistenceHelper
{

    private init(){}

    // MARK: - Core Data stack
    static var context: NSManagedObjectContext{
        return persistentContainer.viewContext
    }

    /**
     Making this public static... so I can keep the mess here
     */
    static public func getSavedPetStoreData() -> [ShowerPersistence]
    {
        var showerPersistence = [ShowerPersistence]()
        let fetchRequest: NSFetchRequest<ShowerPersistence> = ShowerPersistence.fetchRequest()
        do {
            // What??? type of error will this throw ?? I guess i'll just catch all types of errors...
            let showerPersistenceItems = try  PersistenceHelper.context.fetch(fetchRequest)

            for shower in showerPersistenceItems
            {
                showerPersistence.append(shower)
            }

        } catch {
            os_log("Failed to obtain Shower Persistence items", type: .error)
        }

        return showerPersistence
    }


    static public var persistentContainer: NSPersistentContainer = {
        /*
         The persistent container for the application. This implementation
         creates and returns a container, having loaded the store for the
         application to it. This property is optional since there are legitimate
         error conditions that could cause the creation of the store to fail.
        */
        let container = NSPersistentContainer(name: "smart_Shower_App")
        container.loadPersistentStores(completionHandler: { (storeDescription, error) in
            if let error = error as NSError? {
                // Replace this implementation with code to handle the error appropriately.
                // fatalError() causes the application to generate a crash log and terminate. You should not use this function in a shipping application, although it may be useful during development.

                /*
                 Typical reasons for an error here include:
                 * The parent directory does not exist, cannot be created, or disallows writing.
                 * The persistent store is not accessible, due to permissions or data protection when the device is locked.
                 * The device is out of space.
                 * The store could not be migrated to the current model version.
                 Check the error message to determine what the actual problem was.
                 */
                fatalError("Unresolved error \(error), \(error.userInfo)")
            }
        })
        return container
    }()

    // MARK: - Core Data Saving support

    static func saveContext () {
        let context = PersistenceHelper.context
        if context.hasChanges {
            do {
                try context.save()
            } catch {
                // Replace this implementation with code to handle the error appropriately.
                // fatalError() causes the application to generate a crash log and terminate. You should not use this function in a shipping application, although it may be useful during development.
                os_log("Failed to saveContext for Shower Persistence.", type: .error)
                let nserror = error as NSError
                fatalError("Unresolved error \(nserror), \(nserror.userInfo)")
            }
        }
    }
}
