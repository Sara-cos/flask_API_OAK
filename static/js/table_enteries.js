// var today = new Date()
// var dd = String(today.getDate()).padStart(2, '0');
// var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
// var yyyy = today.getFullYear();

// If the todays data is needed
// today = mm+'-'+dd+'-'+yyyy;
// rev_today = yyyy+'-'+mm+'-'+dd

var today = new Date().format('Y-m-d')

// Else if other date data needed, date is taken and passed to func below


// getData.onclick = () => {
//     fetch('http://127.0.0.1:5000/data/')
//       .then(res => res.json())
//       .then((out) => {
//         let jsonData = JSON.parse(out);
//         for (let i = 0; i < jsonData.rev_today.length; i++) {
//             for (const [key, value] of Object.entries(jsonData.rev_today)){
//                 let key_id = key
//                 myData.innerHTML +=
//                    "<tr><td>" + key_id.ID_KEY + "</td>" +
//                    "<td align='right'>" + key_id.name + "</td>" +
//                    "<td align='right'>" + key_id.login_time + "</td>" +
//                    "<td align='right'>" + key_id.logout_time + "</td></tr>";
//             }
//         };
//       })
//       .catch(err => console.error(err));
//   }



//   fetch("http://127.0.0.1:5000/data/").then(
//     res => {
//         res.json().then(
//             data => {
//                 console.log(data);
//                 if (data.length > 0) {

//                     var temp = "";
//                     for (const [key, value] of Object.entries(data.today)){
//                       console.log(key)
//                     }
//                   //   data.forEach((itemData) => {
//                   //     temp += "<tr>";
//                   //     temp += "<td>" + itemData.id + "</td>";
//                   //     temp += "<td>" + itemData.employee_name + "</td>";
//                   //     temp += "<td>" + itemData.employee_salary + "</td>";
//                   //   });
//                     document.getElementById('data').innerHTML = temp;
//                   }
//                 }
//               )
//             }
//           )
// }