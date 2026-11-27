import UIKit
import Capacitor

// écran principal de l'appli : celui de Capacitor, avec le module « Continuer avec Apple » en plus
class BlizViewController: CAPBridgeViewController {
    override open func capacitorDidLoad() {
        bridge?.registerPluginInstance(BlizApplePlugin())
    }
}
