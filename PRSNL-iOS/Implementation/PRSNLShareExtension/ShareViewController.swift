import UIKit
import Social
import CoreData
import MobileCoreServices
import UniformTypeIdentifiers

class ShareViewController: UIViewController {
    
    @IBOutlet weak var contentTextView: UITextView!
    @IBOutlet weak var notesTextView: UITextView!
    
    private var sharedText: String?
    private var sharedURL: URL?
    private var sharedImages: [UIImage] = []
    
    // Core Data managed object context
    private lazy var managedObjectContext: NSManagedObjectContext = {
        let container = getPersistentContainer()
        let context = container.viewContext
        context.automaticallyMergesChangesFromParent = true
        return context
    }()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Extract the shared content
        extractSharedContent()
    }
    
    private func getPersistentContainer() -> NSPersistentContainer {
        let appGroupIdentifier = "group.ai.prsnl.shared"
        
        let container = NSPersistentContainer(name: "PRSNLModel")
        
        // Configure the container to use the app group container URL
        if let storeURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier)?
            .appendingPathComponent("PRSNLModel.sqlite") {
            
            let storeDescription = NSPersistentStoreDescription(url: storeURL)
            container.persistentStoreDescriptions = [storeDescription]
        }
        
        container.loadPersistentStores { (storeDescription, error) in
            if let error = error as NSError? {
                fatalError("Failed to load persistent stores: \(error), \(error.userInfo)")
            }
        }
        
        return container
    }
    
    private func extractSharedContent() {
        let extensionContext = self.extensionContext
        
        if let inputItems = extensionContext?.inputItems as? [NSExtensionItem] {
            for inputItem in inputItems {
                if let attachments = inputItem.attachments {
                    for itemProvider in attachments {
                        // Check for URL
                        if itemProvider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                            itemProvider.loadItem(forTypeIdentifier: UTType.url.identifier, options: nil) { [weak self] (url, error) in
                                if let url = url as? URL {
                                    DispatchQueue.main.async {
                                        self?.sharedURL = url
                                        self?.contentTextView.text = url.absoluteString
                                    }
                                }
                            }
                        }
                        
                        // Check for text
                        else if itemProvider.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
                            itemProvider.loadItem(forTypeIdentifier: UTType.plainText.identifier, options: nil) { [weak self] (text, error) in
                                if let text = text as? String {
                                    DispatchQueue.main.async {
                                        self?.sharedText = text
                                        self?.contentTextView.text = text
                                    }
                                }
                            }
                        }
                        
                        // Check for images
                        else if itemProvider.hasItemConformingToTypeIdentifier(UTType.image.identifier) {
                            itemProvider.loadItem(forTypeIdentifier: UTType.image.identifier, options: nil) { [weak self] (image, error) in
                                if let url = image as? URL, let data = try? Data(contentsOf: url), let image = UIImage(data: data) {
                                    DispatchQueue.main.async {
                                        self?.sharedImages.append(image)
                                        self?.contentTextView.text = "Image shared"
                                    }
                                } else if let image = image as? UIImage {
                                    DispatchQueue.main.async {
                                        self?.sharedImages.append(image)
                                        self?.contentTextView.text = "Image shared"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    @IBAction func cancelTapped(_ sender: UIBarButtonItem) {
        let error = NSError(domain: "ai.prsnl.shareextension", code: 0, userInfo: [NSLocalizedDescriptionKey: "User cancelled"])
        extensionContext?.cancelRequest(withError: error)
    }
    
    @IBAction func saveTapped(_ sender: UIBarButtonItem) {
        saveToSharedContainer()
    }
    
    private func saveToSharedContainer() {
        let context = managedObjectContext
        
        // Create a new Item entity
        let entityName = "Item"
        guard let entity = NSEntityDescription.entity(forEntityName: entityName, in: context) else {
            completeWithError("Failed to create entity")
            return
        }
        
        let newItem = NSManagedObject(entity: entity, insertInto: context)
        
        // Set the properties
        let now = Date()
        
        newItem.setValue(UUID(), forKey: "id")
        newItem.setValue(now, forKey: "createdAt")
        newItem.setValue(now, forKey: "updatedAt")
        
        // Determine content type and set content
        if let url = sharedURL {
            newItem.setValue("url", forKey: "type")
            newItem.setValue(url.absoluteString, forKey: "content")
            newItem.setValue(url.absoluteString, forKey: "title")
        } else if let text = sharedText {
            newItem.setValue("text", forKey: "type")
            newItem.setValue(text, forKey: "content")
            
            // Use first line as title or first few characters
            let lines = text.components(separatedBy: .newlines)
            if let firstLine = lines.first, !firstLine.isEmpty {
                newItem.setValue(firstLine, forKey: "title")
            } else {
                let title = String(text.prefix(30))
                newItem.setValue(title, forKey: "title")
            }
        } else if !sharedImages.isEmpty {
            newItem.setValue("image", forKey: "type")
            if let imageData = sharedImages.first?.jpegData(compressionQuality: 0.8) {
                newItem.setValue(imageData, forKey: "content")
            }
            newItem.setValue("Shared Image", forKey: "title")
        }
        
        // Set notes from the notes text view
        if let notes = notesTextView.text, !notes.isEmpty {
            newItem.setValue(notes, forKey: "notes")
        }
        
        // Save the context
        do {
            try context.save()
            completeRequest()
        } catch {
            print("Failed to save to Core Data: \(error)")
            completeWithError("Failed to save: \(error.localizedDescription)")
        }
    }
    
    private func completeRequest() {
        extensionContext?.completeRequest(returningItems: nil, completionHandler: nil)
    }
    
    private func completeWithError(_ message: String) {
        let error = NSError(domain: "ai.prsnl.shareextension", code: 1, userInfo: [NSLocalizedDescriptionKey: message])
        extensionContext?.cancelRequest(withError: error)
    }
}