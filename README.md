# Linkwarden for Omarchy

Save a link to Linkwarden without leaving your current workspace. Click the chain-link icon in the Omarchy bar, paste an address, and press **Enter**. The bookmark goes to **Unorganized**, ready to sort later.

The widget is for people who want a quick capture inbox on their desktop without installing a browser extension. It works with self-hosted Linkwarden and Linkwarden Cloud.

## Install

Requires Omarchy's Quickshell-based desktop (tested on Omarchy 4.5.0), Python 3, `secret-tool` from `libsecret`, and a desktop keyring that provides Secret Service. The laptop needs HTTPS access to your Linkwarden instance.

```sh
omarchy plugin add https://github.com/CallMeBakugo/omarchy-linkwarden.git --enable
```

## Connect Linkwarden

1. In Linkwarden, open **Settings → Access Tokens** and create a token for this widget.
2. Right-click the chain-link icon in the bar to open **Settings**.
3. Enter your instance address, such as `https://links.example.com`. Use `https://cloud.linkwarden.app` for Linkwarden Cloud. The address takes an optional port and no path. The widget assumes HTTPS if you omit the scheme.
4. Paste the token into the masked **Linkwarden access token** field and click **Save settings**.

The server address and token are stored together in your desktop keyring. Repeat the setup to replace either one.

## Save a link

Left-click the icon, paste a full HTTP or HTTPS URL, and press **Enter** or click **Save link**. **Saved to Unorganized** confirms the server returned the new bookmark in that collection. A rejected or unconfirmed save leaves your URL in the field. If the widget cannot confirm the save, check Linkwarden before retrying to avoid duplicates.

## Troubleshooting

- **Could not access the desktop keyring** — Make sure a Secret Service provider such as GNOME Keyring is running and unlocked.
- **Linkwarden denied access** — Check the instance address and replace the token if it expired or was revoked.
- **Save could not be confirmed** — Check that your instance is reachable from the laptop over HTTPS, that your system trusts its certificate, and that the API is available directly at `/api/v1/links`. The widget rejects redirects.

## Privacy and implementation

The widget reads only the URL you enter in its popup. It does not monitor the clipboard, connect to your browser, or send telemetry. It passes form input to its Python helper through standard input and uses Linkwarden's official API over HTTPS. The helper sends the token only to the configured endpoint and does not follow redirects. Linkwarden handles its usual metadata retrieval and preservation on the server.

- [Panel.qml](Panel.qml) draws the Quickshell bar button and manages the popup.
- [linkwarden.py](linkwarden.py) validates input, calls `secret-tool`, and sends the HTTPS request.
- [Linkwarden create-link API](https://docs.linkwarden.app/api/create-link)

## Update or remove

```sh
omarchy plugin update bakugo.linkwarden
omarchy plugin remove bakugo.linkwarden
```

To also delete the saved connection from your keyring, run:

```sh
secret-tool clear application bakugo.linkwarden purpose connection
```

Revoke the token under **Settings → Access Tokens** in Linkwarden when you no longer need it.

## Development

```sh
omarchy plugin validate .
python3 -m unittest discover -s tests
```

The tests mock the keyring and network, so they need no server or token.

## License

[MIT](LICENSE).
