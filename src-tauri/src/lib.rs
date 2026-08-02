use std::{
    net::{SocketAddr, TcpListener, TcpStream},
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::{Duration, Instant},
};

use tauri::{Manager, RunEvent, WebviewUrl, WebviewWindowBuilder};

struct BackendProcess(Mutex<Option<Child>>);

impl BackendProcess {
    fn stop(&self) {
        let Ok(mut guard) = self.0.lock() else {
            return;
        };
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

fn free_loopback_port() -> Result<u16, String> {
    TcpListener::bind(("127.0.0.1", 0))
        .and_then(|listener| listener.local_addr())
        .map(|address| address.port())
        .map_err(|error| format!("No se pudo reservar un puerto local: {error}"))
}

fn backend_path(resource_dir: PathBuf) -> PathBuf {
    resource_dir
        .join("binaries")
        .join("FacelessCreatorBackend")
        .join("FacelessCreatorBackend.exe")
}

fn wait_until_ready(address: SocketAddr, child: &mut Child) -> Result<(), String> {
    let deadline = Instant::now() + Duration::from_secs(45);
    while Instant::now() < deadline {
        if TcpStream::connect_timeout(&address, Duration::from_millis(250)).is_ok() {
            return Ok(());
        }
        if let Some(status) = child
            .try_wait()
            .map_err(|error| format!("No se pudo comprobar el backend: {error}"))?
        {
            return Err(format!("El backend terminó antes de iniciar ({status})."));
        }
        thread::sleep(Duration::from_millis(150));
    }
    Err("El backend no respondió dentro de 45 segundos.".to_owned())
}

fn start_backend(app: &tauri::AppHandle) -> Result<(Child, u16), String> {
    let port = free_loopback_port()?;
    let resource_dir = app
        .path()
        .resource_dir()
        .map_err(|error| format!("No se encontró el directorio de recursos: {error}"))?;
    let executable = backend_path(resource_dir);
    if !executable.is_file() {
        return Err(format!(
            "No se encontró el backend empaquetado: {}",
            executable.display()
        ));
    }
    let port_argument = port.to_string();
    let parent_argument = std::process::id().to_string();
    let mut child = Command::new(&executable)
        .args([
            "--no-browser",
            "--port",
            &port_argument,
            "--parent-pid",
            &parent_argument,
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|error| format!("No se pudo iniciar el backend: {error}"))?;
    let address = SocketAddr::from(([127, 0, 0, 1], port));
    if let Err(error) = wait_until_ready(address, &mut child) {
        let _ = child.kill();
        let _ = child.wait();
        return Err(error);
    }
    Ok((child, port))
}

pub fn run() {
    let app = tauri::Builder::default()
        .setup(|app| {
            let (backend, port) = start_backend(app.handle())?;
            app.manage(BackendProcess(Mutex::new(Some(backend))));
            let url = format!("http://127.0.0.1:{port}")
                .parse()
                .map_err(|error| format!("URL local inválida: {error}"))?;
            WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url))
                .title("FacelessCreator")
                .inner_size(1440.0, 900.0)
                .min_inner_size(1100.0, 700.0)
                .resizable(true)
                .center()
                .build()?;
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error al construir FacelessCreator desktop");

    app.run(|handle, event| {
        if matches!(event, RunEvent::Exit | RunEvent::ExitRequested { .. }) {
            handle.state::<BackendProcess>().stop();
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reserves_a_loopback_port() {
        let port = free_loopback_port().expect("port");
        assert_ne!(port, 0);
    }

    #[test]
    fn builds_backend_resource_path() {
        let path = backend_path(PathBuf::from("resources"));
        assert_eq!(
            path,
            PathBuf::from("resources/binaries/FacelessCreatorBackend/FacelessCreatorBackend.exe")
        );
    }
}
