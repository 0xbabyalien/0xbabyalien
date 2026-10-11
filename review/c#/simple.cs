using System;

namespace Review
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("========================================");
            Console.WriteLine("       SIMPLE SHOPPING CALCULATOR       ");
            Console.WriteLine("========================================");

            Console.Write("Enter item name: ");
            string itemName = Console.ReadLine();

            Console.Write("Enter item price ($): ");
            double itemPrice = Convert.ToDouble(Console.ReadLine());

            Console.Write("Enter quantity: ");
            int quantity = Convert.ToInt32(Console.ReadLine());

            double subtotal = itemPrice * quantity;
            double tax = subtotal * 0.10;
            double totalPrice = subtotal + tax;

            Console.WriteLine("\n----------------------------------------");
            Console.WriteLine("             PURCHASE SUMMARY           ");
            Console.WriteLine("----------------------------------------");
            Console.WriteLine($"Item        : {itemName}");
            Console.WriteLine($"Price       : ${itemPrice:F2}");
            Console.WriteLine($"Quantity    : {quantity}");
            Console.WriteLine($"Subtotal    : ${subtotal:F2}");
            Console.WriteLine($"Tax (10%)   : ${tax:F2}");
            Console.WriteLine($"Total       : ${totalPrice:F2}");
            Console.WriteLine("========================================");
            Console.WriteLine("Thank you for your purchase!");
        }
    }
}
