Writing GUI applications in Python is hard, so let's make it easy and simple!

Modular interface concept. User does not need the interface to constantly occupy the workspace. Need for it appears only when performing tasks.

Thus, the entire interface is divided into modules. They appear at the moment of interaction with user.

This is a set of widgets that can always be extended. Widgets can have multiple implementations: Terminal, Qt, GTK. And user simply chooses the one that suits him best.

If user minimizes or closes the module, then it's okay. Program will send a notification or open module when needed.

One module for one specific task. Management of programs that call modules is performed using hotkeys.

This concept makes user experience consistent and productive. But it is not suitable for tasks that require full concentration, such as editing documents and games.
