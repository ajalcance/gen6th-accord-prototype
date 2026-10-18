import PassportStudio from "./legacy-passport-studio";
import { initialConsole } from "./legacy-passport/console-fixtures";

// Historical scenario acceptance is explicit; the application defaults to no examples.
export default function ConsoleTestStudio() {
  return <PassportStudio initialState={initialConsole()} />;
}
