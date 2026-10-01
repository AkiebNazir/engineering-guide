// REAL-WORLD EXAMPLE: tiaguinho/gosoap (External 2)
// Demonstrates: Dynamic SOAP client invocation without requiring code generation.
package main

import (
	"fmt"
	// "github.com/tiaguinho/gosoap"
)

func main() {
	// 1. Initialize client dynamically from WSDL
	// soap, err := gosoap.SoapClient("http://www.dataaccess.com/webservicesserver/numberconversion.wso?WSDL")
	// if err != nil {
	// 	panic(err)
	// }
	
	// 2. Define parameters as a map
	// params := gosoap.Params{"ubiNum": 500}
	
	// 3. Invoke method dynamically
	// res, err := soap.Call("NumberToWords", params)
	// if err != nil {
	// 	panic(err)
	// }

	// 4. Unmarshal response
	// var result string
	// res.Unmarshal(&result)
	// fmt.Println("Gosoap response:", result)
	
	fmt.Println("Gosoap allows dynamic WSDL calls. See comments for usage.")
}
