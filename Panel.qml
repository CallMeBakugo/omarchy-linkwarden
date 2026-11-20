import QtQuick
import Quickshell.Io
import qs.Commons
import qs.Ui
import qs.Ui as Ui

Panel {
  id: root
  moduleName: "bakugo.linkwarden"

  property bool tokenMode: false
  property string status: ""
  readonly property string helperPath: Qt.resolvedUrl("linkwarden.py").toString().replace(/^file:\/\//, "")
  readonly property var resultKeys: [
    "stored", "saved", "missing", "unauthorized", "invalidUrl", "invalidToken",
    "invalidServer", "keyring", "duplicate", "busy", "unconfirmed", "destination", "rejected"
  ]

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  function switchTo(settings) {
    if (worker.running) {
      if (!opened) open()
      return
    }
    if (opened && tokenMode === settings) {
      close()
      return
    }
    tokenMode = settings
    status = ""
    tokenField.clear()
    open()
    Qt.callLater(() => popup.focusTarget.forceActiveFocus())
  }

  function submit() {
    if (worker.running) return
    if (tokenMode) {
      if (!serverField.text.trim() || !tokenField.text.trim()) return
      worker.input = JSON.stringify({ server: serverField.text, token: tokenField.text })
    } else {
      if (!urlField.text.trim()) return
      worker.input = urlField.text
    }
    worker.command = ["/usr/bin/python3", decodeURIComponent(helperPath), tokenMode ? "store" : "save"]
    worker.running = true
    if (tokenMode) tokenField.clear()
  }

  onOpenedChanged: if (!opened) tokenField.clear()

  Translations {
    id: strings
    directory: Qt.resolvedUrl("i18n")
  }

  Process {
    id: worker
    property string input: ""
    stdinEnabled: true
    stdout: StdioCollector { id: output; waitForEnd: true }
    onStarted: {
      write(input + "\n")
      input = ""
    }
    onExited: function(exitCode) {
      input = ""
      const result = output.text.trim()
      root.status = exitCode === 0 && root.resultKeys.includes(result) ? result : "failed"
      if (root.status === "saved" || root.status === "destination") urlField.clear()
    }
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "\uf0c1"
    tooltipText: strings.t("tooltip")
    onPressed: function(mouseButton) {
      if (mouseButton === Qt.LeftButton || mouseButton === Qt.RightButton)
        root.switchTo(mouseButton === Qt.RightButton)
    }
  }

  KeyboardPanel {
    id: popup
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: root.tokenMode ? serverField : urlField
    contentWidth: fittedContentWidth(Style.space(360))
    contentHeight: fittedContentHeight(panelColumn.implicitHeight, Style.space(300))

    Column {
      id: panelColumn
      width: parent.width
      spacing: Style.space(8)

      Ui.TextField {
        id: urlField
        width: parent.width
        visible: !root.tokenMode
        readOnly: worker.running
        maximumLength: 4096
        foreground: root.barForeground
        placeholderText: strings.t("url")
        onAccepted: root.submit()
        Keys.onEscapePressed: root.close()
        onTextEdited: if (!worker.running) root.status = ""
      }

      Ui.TextField {
        id: serverField
        width: parent.width
        visible: root.tokenMode
        readOnly: worker.running
        maximumLength: 300
        foreground: root.barForeground
        placeholderText: strings.t("server")
        onAccepted: tokenField.forceActiveFocus()
        Keys.onEscapePressed: root.close()
        onTextEdited: if (!worker.running) root.status = ""
      }

      Ui.TextField {
        id: tokenField
        width: parent.width
        visible: root.tokenMode
        readOnly: worker.running
        maximumLength: 4096
        foreground: root.barForeground
        placeholderText: strings.t("token")
        password: true
        inputMethodHints: Qt.ImhHiddenText | Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
        onAccepted: root.submit()
        Keys.onEscapePressed: root.close()
        onTextEdited: if (!worker.running) root.status = ""
      }

      Row {
        spacing: Style.space(4)

        WidgetButton {
          bar: root.bar
          text: strings.t(root.tokenMode ? "store" : "save")
          enabled: !worker.running && (root.tokenMode
            ? Boolean(serverField.text.trim() && tokenField.text.trim())
            : Boolean(urlField.text.trim()))
          dimmed: !enabled
          onPressed: function(mouseButton) {
            if (mouseButton === Qt.LeftButton) root.submit()
          }
        }

        WidgetButton {
          bar: root.bar
          visible: !root.tokenMode
          text: strings.t("setup")
          enabled: !worker.running
          onPressed: function(mouseButton) {
            if (mouseButton === Qt.LeftButton) root.switchTo(true)
          }
        }
      }

      Text {
        width: parent.width
        visible: text !== ""
        textFormat: Text.PlainText
        text: worker.running ? strings.t(root.tokenMode ? "storing" : "saving")
          : root.status === "" ? "" : strings.t(root.status)
        color: root.barForeground
        font.family: Style.font.family
        font.pixelSize: Style.font.caption
        wrapMode: Text.Wrap
      }
    }
  }
}
