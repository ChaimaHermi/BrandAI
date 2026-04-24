import { Link } from "react-router-dom";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { BlobBackground } from "@/components/ui/BlobBackground";

/**
 * Politique de confidentialité — URL publique pour exigences Meta / stores / RGPD (base informative).
 * À adapter (coordonnées, DPO, finalités précises) selon votre déploiement réel.
 */
export default function PrivacyPage() {
  return (
    <div className="relative flex min-h-screen flex-col">
      <BlobBackground />
      <Navbar variant="landing" />
      <main className="relative z-10 flex flex-1 flex-col px-4 pb-16 pt-24 md:px-6">
        <div className="mx-auto w-full max-w-3xl">
          <p className="mb-2 text-sm text-ink-muted">
            <Link to="/" className="font-medium text-brand hover:underline">
              ← Accueil
            </Link>
          </p>
          <h1 className="mb-2 text-3xl font-bold tracking-tight text-ink">
            Politique de confidentialité
          </h1>
          <p className="mb-10 text-sm text-ink-muted">
            Dernière mise à jour : 20 avril 2026 · BrandAI (« nous », « le service »)
          </p>

          <div className="space-y-8 text-[15px] leading-relaxed text-ink-body">
            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">1. Responsable du traitement</h2>
              <p>
                Le présent service BrandAI est proposé dans un cadre de projet / démonstration. Le
                responsable du traitement des données personnelles est la personne ou l’entité que vous
                identifiez comme éditeur du site (à compléter : dénomination sociale, adresse, contact).
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">2. Données collectées</h2>
              <p>Nous pouvons traiter notamment :</p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong>Compte :</strong> identifiant, nom ou pseudonyme, adresse e-mail, données de
                  connexion (ex. authentification tierce si activée).
                </li>
                <li>
                  <strong>Projet / idées :</strong> contenus que vous saisissez pour générer analyses,
                  identité de marque, contenus, etc.
                </li>
                <li>
                  <strong>Technique :</strong> journaux, adresse IP, type de navigateur, horodatages, à
                  des fins de sécurité et de bon fonctionnement.
                </li>
                <li>
                  <strong>Réseaux sociaux (optionnel) :</strong> lorsque vous connectez Facebook / Meta,
                  Instagram ou LinkedIn pour publier du contenu, des jetons d’accès et identifiants de
                  page ou de profil peuvent être traités conformément aux conditions de ces plateformes.
                </li>
              </ul>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">3. Finalités et bases légales</h2>
              <p>
                Fourniture du service, création de compte, amélioration du produit, support,
                sécurité, respect d’obligations légales ; lorsque le RGPD s’applique, le traitement repose
                notamment sur l’exécution du contrat, l’intérêt légitime (sécurité) ou votre consentement
                lorsque requis (ex. cookies non essentiels ou intégrations optionnelles).
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">4. Destinataires et sous-traitants</h2>
              <p>
                Hébergeur, prestataires d’infrastructure ou d’IA selon votre configuration, et
                plateformes tierces que vous autorisez explicitement (Meta, LinkedIn, etc.). Ces acteurs
                traitent des données selon leurs propres politiques lorsque vous utilisez leurs services.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">5. Durée de conservation</h2>
              <p>
                Les données sont conservées le temps nécessaire aux finalités ci-dessus, puis supprimées ou
                anonymisées, sauf obligation légale de conservation plus longue.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">6. Vos droits</h2>
              <p>
                Selon votre juridiction, vous pouvez disposer d’un droit d’accès, de rectification,
                d’effacement, de limitation, d’opposition, de portabilité et du retrait du consentement.
                Pour l’exercer, contactez le responsable du traitement à l’adresse indiquée sur le site ou
                via votre espace utilisateur lorsque disponible.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">7. Sécurité</h2>
              <p>
                Nous mettons en œuvre des mesures techniques et organisationnelles appropriées pour
                protéger vos données contre l’accès non autorisé, la perte ou l’altération.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">8. Modifications</h2>
              <p>
                Cette politique peut être mise à jour. La date en tête de page sera ajustée ; nous vous
                invitons à la consulter régulièrement.
              </p>
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">9. Contact</h2>
              <p>
                Pour toute question relative à cette politique ou à vos données personnelles, écrivez à
                l’éditeur du service aux coordonnées publiées sur le site (à compléter avec un e-mail ou
                formulaire de contact dédié).
              </p>
            </section>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
