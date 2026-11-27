import Foundation
import Capacitor
import AuthenticationServices

// « Continuer avec Apple » : la feuille d'Apple (Face ID) donne un jeton que le site passe à Firebase.
// Aucun SDK Firebase natif : le compte reste géré par le code web (platoz.html), comme avant.
@objc(BlizApplePlugin)
public class BlizApplePlugin: CAPPlugin, CAPBridgedPlugin, ASAuthorizationControllerDelegate, ASAuthorizationControllerPresentationContextProviding {
    public let identifier = "BlizApplePlugin"
    public let jsName = "BlizApple"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "signIn", returnType: CAPPluginReturnPromise)
    ]
    private var pending: CAPPluginCall?

    @objc func signIn(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            if let old = self.pending { old.reject("Remplacé", "canceled") }
            let request = ASAuthorizationAppleIDProvider().createRequest()
            request.requestedScopes = [.fullName]
            // le site envoie le SHA-256 d'un nombre au hasard ; Firebase vérifie qu'il correspond
            request.nonce = call.getString("nonce")
            self.pending = call
            let controller = ASAuthorizationController(authorizationRequests: [request])
            controller.delegate = self
            controller.presentationContextProvider = self
            controller.performRequests()
        }
    }

    public func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        return self.bridge?.webView?.window ?? ASPresentationAnchor()
    }

    public func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
        guard let call = pending else { return }
        pending = nil
        guard let cred = authorization.credential as? ASAuthorizationAppleIDCredential,
              let data = cred.identityToken, let token = String(data: data, encoding: .utf8) else {
            call.reject("Pas de jeton Apple", "failed")
            return
        }
        var code = ""
        if let c = cred.authorizationCode { code = String(data: c, encoding: .utf8) ?? "" }
        call.resolve([
            "idToken": token,
            "authorizationCode": code,
            "givenName": cred.fullName?.givenName ?? "",
            "familyName": cred.fullName?.familyName ?? ""
        ])
    }

    public func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        guard let call = pending else { return }
        pending = nil
        let canceled = (error as? ASAuthorizationError)?.code == .canceled
        call.reject(error.localizedDescription, canceled ? "canceled" : "failed")
    }
}
