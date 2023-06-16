
import modules.movment as mv
from dotenv import dotenv_values
import multiprocessing as mp
movment_pipe = mp.Pipe()

movement = mv.Movment(movment_pipe[0],dotenv_values('.env'))

# make an menu from self.move_list_words  and exec a function from self.move_list
def test_menu():
    print("Select a movement function to execute")
    for i in range(len(movement.move_list_words)):
        print("["+str(i)+"] "+movement.move_list_words[i])
    print("[q] Quit")
    while True:
        choice = input("Choice: ")
        if choice == "q":
            break
        elif choice.isdigit():
            choice = int(choice)
            if choice < len(movement.move_list_words):
                try:
                    movement.move_list[choice]()
                except Exception as e:
                    print(e)
                except:
                    print("Stopped")
                movement.reset_position()
            else:
                print("Invalid choice")
        else:
            print("Invalid choice")

test_menu()