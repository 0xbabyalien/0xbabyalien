import java.util.Scanner;

public class star{
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);

        System.out.println("========================================");
        System.out.println("          STAR PATTERN GENERATOR        ");
        System.out.println("========================================");
        System.out.print("Enter number of rows: ");
        int rows = scanner.nextInt();

        System.out.println("\n1. Right Triangle Pattern:");
        for (int i = 1; i <= rows; i++) {
            for (int j = 1; j <= i; j++) {
                System.out.print("* ");
            }
            System.out.println();
        }

        System.out.println("\n2. Pyramid Pattern:");
        for (int i = 1; i <= rows; i++) {
            for (int j = i; j < rows; j++) {
                System.out.print(" ");
            }
            for (int k = 1; k <= (2 * i - 1); k++) {
                System.out.print("*");
            }
            System.out.println();
        }

        System.out.println("========================================");
        scanner.close();
    }
}
