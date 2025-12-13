use pyoxidizer::pyembed;

fn main() {
    pyembed::MainPythonInterpreter::new().run(|py| {
        py.run(
            r#"
import sys
from clipfix.main import main
sys.exit(main())
"#,
            None,
            None,
        )
    });
}
