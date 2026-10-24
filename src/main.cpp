#include "appearance.h"
#include "mcp_server.h"
#include "trickster_version.h"
#include "window.h"
#include <QApplication>
#include <QCommandLineParser>
#include <QDir>
#include <QFile>
#include <QFont>
#include <QJsonDocument>
#include <QPalette>
#include <QSaveFile>
#include <QSettings>
#include <QSurfaceFormat>
#include <QTextStream>
#include <QTimer>
int main(int argc, char **argv) {
    QSurfaceFormat fmt;
    fmt.setVersion(2, 1);
    fmt.setProfile(QSurfaceFormat::CompatibilityProfile);
    fmt.setDepthBufferSize(24);
    fmt.setSamples(4);
    QSurfaceFormat::setDefaultFormat(fmt);
    QApplication app(argc, argv);
    app.setOrganizationName("Trickster");
    app.setApplicationName("Trickster");
    app.setApplicationVersion(TRICKSTER_VERSION);
    trickster::applyAppearance(app);
    QCommandLineParser parser;
    parser.setApplicationDescription("Trickster — character animation editor");
    parser.addHelpOption();
    parser.addVersionOption();
    parser.addOption({"build-info", "Print product version and source build ID"});
    parser.addPositionalArgument("file", "Character (.fbx/.glb/.gltf) or project (.trickster)");
    parser.addOption({"demo", "Open the animated built-in demo"});
    parser.addOption({"generate-demo", "Write demo project and GLB into directory", "directory"});
    parser.addOption({"screenshot", "Save window and viewport screenshots, then exit", "path"});
    parser.addOption({"mcp", "Start the local MCP server (can also be controlled from Automation)"});
    parser.addOption({"mcp-port", "MCP port; 0 selects a free port", "port"});
    parser.addOption({"mcp-config", "Write local connection JSON when starting MCP", "path"});
    parser.process(app);
    if (parser.isSet("build-info")) {
        QTextStream(stdout) << "Trickster " << TRICKSTER_VERSION << " (" << TRICKSTER_BUILD_ID << ")\n";
        return 0;
    }
    if ((parser.isSet("mcp-port") || parser.isSet("mcp-config")) && !parser.isSet("mcp")) {
        qCritical("--mcp-port/--mcp-config require --mcp");
        return 2;
    }
    trickster::Window window;
    if (parser.isSet("demo"))
        window.document().demo();
    if (parser.isSet("generate-demo"))
        window.saveDemo(parser.value("generate-demo"));
    if (!parser.positionalArguments().isEmpty())
        window.open(parser.positionalArguments().first());
    if (parser.isSet("mcp")) {
        bool valid = false;
        uint port = (parser.isSet("mcp-port") ? parser.value("mcp-port")
                                              : QSettings().value("automation/port", 18430).toString())
                        .toUInt(&valid);
        if (!valid || port > 65535) {
            qCritical("Invalid MCP port");
            return 2;
        }
        if (!window.mcpServer()->start(quint16(port))) {
            qCritical("MCP start failed: %s", qPrintable(window.mcpServer()->lastError()));
            return 2;
        }
        if (parser.isSet("mcp-config")) {
            QSaveFile config(parser.value("mcp-config"));
            if (!config.open(QIODevice::WriteOnly) ||
                config.write(QJsonDocument(window.mcpServer()->connectionConfig()).toJson()) < 0 ||
                !config.commit()) {
                qCritical("Cannot write MCP connection file");
                return 2;
            }
        }
    }
    window.show();
    if (parser.isSet("screenshot")) {
        QString path = parser.value("screenshot");
        QTimer::singleShot(1500, &window, [&window, path, &app] {
            QDir().mkpath(QFileInfo(path).absolutePath());
            bool ok = window.grab().save(path);
            window.viewport->grab().save(QFileInfo(path).absolutePath() + "/viewport.png");
            window.document().undo.setClean();
            app.exit(ok ? 0 : 2);
        });
    }
    return app.exec();
}
