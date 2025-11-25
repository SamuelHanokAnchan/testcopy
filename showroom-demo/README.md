# ShowroomDemo

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 20.1.6.

## Environment / Secrets Handling

Lokale Entwicklung:
1. Kopiere `src/environments/environment.dev.sample.ts` nach `src/environments/environment.dev.ts` (Datei ist in `.gitignore`).
2. Trage dort deinen lokalen API Key und optional die Syncfusion Lizenz ein (oder nutze Runtime-Injektion).
3. Starte mit `npm start` (nutzt Proxy + dev environment).

Production Build (CI/CD):
1. In `environment.prod.ts` stehen nur Platzhalter (`__API_BASE_URL__`, `__API_KEY__`, `__SYNCFUSION_LICENSE__`).
2. Der GitHub Actions Workflow ersetzt die Platzhalter direkt per `sed` bevor gebaut wird.
3. Lokal kannst du sie manuell ersetzen oder ein eigenes kleines Script/One‑Liner verwenden (optional).

Erforderliche GitHub Secrets (Repository Settings > Secrets and variables > Actions):
* `API_BASE_URL` – z.B. `https://<dein-backend>/api`
* `API_KEY` – geheimer Backend API Key
* `SYNCFUSION_LICENSE` – dein Syncfusion Lizenzschlüssel

Hinweis: Im Repository Workflow werden die Secrets direkt in `environment.prod.ts` ersetzt.

Wichtig: Keine echten Secrets in Git committen – nur Platzhalter und Sample-Dateien.

Automatischer Build Workflow: siehe `.github/workflows/azure-static-web-app.yml`.

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Karma](https://karma-runner.github.io) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
