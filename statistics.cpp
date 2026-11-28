#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include <string>
#include <numeric>
#include <map>
namespace py = pybind11;
double calculate_sum(const std::vector<double>& amounts) {
    return std::accumulate(amounts.begin(), amounts.end(), 0.0);
}
std::map<std::string, double> sum_by_category(
    const std::vector<std::string>& categories,
    const std::vector<double>& amounts) 
{
    std::map<std::string, double> result;
    if (categories.size() != amounts.size()) {
        throw std::runtime_error("Category and amount sizes do not match.");
    }
    for (size_t i = 0; i < categories.size(); ++i) {
        result[categories[i]] += amounts[i];
    }
    return result;
}
PYBIND11_MODULE(cpp_stats, m) {
    m.doc() = "C++ statistics module for finance app";
    m.def("calculate_sum", &calculate_sum, "Calculate total amount");
    m.def("sum_by_category", &sum_by_category, "Sum amounts grouped by category");
}